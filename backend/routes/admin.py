"""Admin routes: users management, approvals, audit logs, settings, seed"""
import os
import sys
import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
import resend
from core.database import db, SOFT_DELETE_FILTER
from core.auth import get_current_user, hash_password
from core.permissions import require_role, get_permissions
from core.websocket import manager
from core.helpers import audit_log, SENDER_EMAIL
from models.schemas import UserRegister, UserUpdate, ApprovalRequest, NotificationSettings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])


# ============ USERS ============
@router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    result = []
    async for u in db.users.find({}):
        result.append({
            "id": str(u["_id"]), "email": u.get("email", ""), "name": u.get("name", ""),
            "role": u.get("role", "user"), "is_active": u.get("is_active", True),
            "created_at": u.get("created_at", "")
        })
    return result

@router.post("/users")
async def create_user(user: UserRegister, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    existing = await db.users.find_one({"email": user.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email deja utilise")
    user_doc = {
        "email": user.email.lower(), "password_hash": hash_password(user.password),
        "name": user.name, "role": user.role, "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(user_doc)
    await audit_log(current_user, "CREATE", "user", str(result.inserted_id), user.name, new_values={"email": user.email, "role": user.role})
    return {"id": str(result.inserted_id), "email": user.email, "name": user.name, "role": user.role}

@router.put("/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnee")
    existing = await db.users.find_one({"_id": ObjectId(user_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    await audit_log(current_user, "UPDATE", "user", user_id, existing.get("name", ""), new_values=update_data)
    return {"id": user_id, **update_data}

@router.delete("/users/{user_id}")
async def deactivate_user(user_id: str, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    if user_id == current_user["_id"]:
        raise HTTPException(status_code=400, detail="Impossible de desactiver votre propre compte")
    existing = await db.users.find_one({"_id": ObjectId(user_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_active": False}})
    await audit_log(current_user, "DEACTIVATE", "user", user_id, existing.get("name", ""))
    return {"message": "Utilisateur desactive"}


# ============ APPROVALS ============
@router.get("/approvals")
async def get_approvals(status: str = None, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    query = {}
    if status:
        query["status"] = status
    result = []
    async for a in db.approval_requests.find(query).sort("created_at", -1).limit(100):
        result.append({
            "id": str(a["_id"]), "requester_id": a.get("requester_id", ""),
            "requester_name": a.get("requester_name", ""), "requester_role": a.get("requester_role", ""),
            "action": a.get("action", ""), "entity_type": a.get("entity_type", ""),
            "entity_id": a.get("entity_id", ""), "entity_name": a.get("entity_name", ""),
            "details": a.get("details", {}), "status": a.get("status", "pending"),
            "reviewed_by": a.get("reviewed_by", ""), "reviewed_at": a.get("reviewed_at", ""),
            "created_at": a.get("created_at", "")
        })
    return result

@router.get("/approvals/count")
async def get_approval_count(current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    count = await db.approval_requests.count_documents({"status": "pending"})
    return {"pending_count": count}

@router.post("/approvals/{approval_id}/approve")
async def approve_request(approval_id: str, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    approval = await db.approval_requests.find_one({"_id": ObjectId(approval_id)})
    if not approval:
        raise HTTPException(status_code=404, detail="Demande non trouvee")
    if approval["status"] != "pending":
        raise HTTPException(status_code=400, detail="Demande deja traitee")
    await db.approval_requests.update_one({"_id": ObjectId(approval_id)}, {"$set": {
        "status": "approved", "reviewed_by": current_user.get("name", current_user.get("email", "")),
        "reviewed_at": datetime.now(timezone.utc).isoformat()
    }})
    action = approval.get("action", "")
    entity_id = approval.get("entity_id", "")
    entity_type = approval.get("entity_type", "")
    if action == "delete_client":
        existing = await db.clients.find_one({"_id": ObjectId(entity_id)})
        if existing:
            appart_ids = existing.get("appartement_ids") or []
            for aid in appart_ids:
                try:
                    await db.appartements.update_one({"_id": ObjectId(aid)}, {"$set": {"statut": "disponible", "client_id": None}})
                except Exception:
                    pass
            await db.clients.update_one({"_id": ObjectId(entity_id)}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat(), "deleted_by": current_user["_id"], "deleted_by_name": current_user.get("name", "")}})
    elif action == "modify_price":
        details = approval.get("details", {})
        new_prix = details.get("new_prix")
        if new_prix:
            await db.appartements.update_one({"_id": ObjectId(entity_id)}, {"$set": {"prix": new_prix}})
    elif action in ("delete_appartement", "delete_prospect"):
        coll = "appartements" if "appartement" in action else "prospects"
        await db[coll].update_one({"_id": ObjectId(entity_id)}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat(), "deleted_by": current_user["_id"]}})
    await audit_log(current_user, "APPROVE", entity_type, entity_id, approval.get("entity_name", ""), new_values={"action": action})
    await manager.broadcast({"type": "approval_processed"})
    asyncio.create_task(send_approval_email(approval.get("requester_name", ""), approval, "approved", current_user.get("name", "")))
    return {"message": "Demande approuvee et action executee"}

@router.post("/approvals/{approval_id}/reject")
async def reject_request(approval_id: str, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    approval = await db.approval_requests.find_one({"_id": ObjectId(approval_id)})
    if not approval:
        raise HTTPException(status_code=404, detail="Demande non trouvee")
    if approval["status"] != "pending":
        raise HTTPException(status_code=400, detail="Demande deja traitee")
    await db.approval_requests.update_one({"_id": ObjectId(approval_id)}, {"$set": {
        "status": "rejected", "reviewed_by": current_user.get("name", current_user.get("email", "")),
        "reviewed_at": datetime.now(timezone.utc).isoformat()
    }})
    await audit_log(current_user, "REJECT", approval.get("entity_type", ""), approval.get("entity_id", ""), approval.get("entity_name", ""))
    await manager.broadcast({"type": "approval_processed"})
    asyncio.create_task(send_approval_email(approval.get("requester_name", ""), approval, "rejected", current_user.get("name", "")))
    return {"message": "Demande rejetee"}


async def send_approval_email(to_email: str, approval: dict, decision: str, reviewer_name: str):
    try:
        if not resend.api_key:
            return
        notification_email = os.environ.get("NOTIFICATION_EMAIL", "")
        if not notification_email:
            return
        color = "#22c55e" if decision == "approved" else "#ef4444"
        status_text = "APPROUVEE" if decision == "approved" else "REJETEE"
        html = f"""<div style="font-family:Arial;max-width:600px;margin:0 auto;"><div style="background:#1E3A5F;color:white;padding:20px;text-align:center;"><h1 style="margin:0;">DJERBA CONSTRUCTION</h1></div><div style="padding:20px;background:#f8f9fa;"><h2 style="color:{color};">Demande {status_text}</h2><p><strong>Action:</strong> {approval.get('action','')}</p><p><strong>Element:</strong> {approval.get('entity_name','')}</p><p><strong>Decideur:</strong> {reviewer_name}</p></div></div>"""
        params = {"from": SENDER_EMAIL, "to": [notification_email], "subject": f"Demande {status_text} - {approval.get('entity_name','')}", "html": html}
        await asyncio.to_thread(resend.Emails.send, params)
    except Exception as e:
        logger.error(f"Approval email error: {e}")


async def send_approval_notification_to_admins(approval_doc: dict):
    try:
        if not resend.api_key:
            return
        notification_email = os.environ.get("NOTIFICATION_EMAIL", "")
        if not notification_email:
            return
        html = f"""<div style="font-family:Arial;max-width:600px;margin:0 auto;"><div style="background:#1E3A5F;color:white;padding:20px;text-align:center;"><h1 style="margin:0;">DJERBA CONSTRUCTION</h1></div><div style="padding:20px;background:#f8f9fa;"><h2 style="color:#f59e0b;">Nouvelle demande d'approbation</h2><p><strong>De:</strong> {approval_doc.get('requester_name','')}</p><p><strong>Action:</strong> {approval_doc.get('action','')}</p><p><strong>Element:</strong> {approval_doc.get('entity_name','')}</p><a href="{os.environ.get('FRONTEND_URL','')}/admin" style="display:inline-block;background:#C41E3A;color:white;padding:12px 24px;text-decoration:none;border-radius:4px;margin-top:16px;">Voir dans le CRM</a></div></div>"""
        params = {"from": SENDER_EMAIL, "to": [notification_email], "subject": f"Approbation requise: {approval_doc.get('action','')} - {approval_doc.get('entity_name','')}", "html": html}
        await asyncio.to_thread(resend.Emails.send, params)
    except Exception as e:
        logger.error(f"Approval notification error: {e}")


# ============ AUDIT LOGS ============
@router.get("/audit-logs")
async def get_audit_logs(action: str = None, entity_type: str = None, user_id: str = None, date_from: str = None, date_to: str = None, search: str = None, limit: int = 200, current_user: dict = Depends(get_current_user)):
    query = {}
    if action:
        query["action"] = action
    if entity_type:
        query["entity_type"] = entity_type
    if user_id:
        query["user_id"] = user_id
    if date_from:
        query["timestamp"] = query.get("timestamp", {})
        query["timestamp"]["$gte"] = date_from
    if date_to:
        query["timestamp"] = query.get("timestamp", {})
        query["timestamp"]["$lte"] = date_to
    if search:
        query["$or"] = [{"entity_name": {"$regex": search, "$options": "i"}}, {"user_name": {"$regex": search, "$options": "i"}}]
    result = []
    async for log in db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit):
        result.append(log)
    return result


# ============ SETTINGS ============
@router.get("/settings/notifications")
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    settings = await db.settings.find_one({"type": "notifications"})
    if not settings:
        return {"email_enabled": False, "notification_emails": []}
    return {"email_enabled": settings.get("email_enabled", False), "notification_emails": settings.get("notification_emails", [])}

@router.put("/settings/notifications")
async def update_notification_settings(settings: NotificationSettings, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    await db.settings.update_one(
        {"type": "notifications"},
        {"$set": {"type": "notifications", "email_enabled": settings.email_enabled, "notification_emails": settings.notification_emails, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": current_user["_id"]}},
        upsert=True
    )
    return {"message": "Parametres mis a jour"}


# ============ ADMIN SEED ============
@router.post("/admin/seed")
async def admin_seed_edimco(current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    apparts_count = await db.appartements.count_documents({})
    if apparts_count > 0:
        return {"message": f"Base deja peuplee: {apparts_count} appartements", "seeded": False}
    residence = await db.residences.find_one({"nom": "EDIMCO"})
    if not residence:
        result = await db.residences.insert_one({"nom": "EDIMCO", "adresse": "EDIMCO, Commune de Bejaia, Wilaya de Bejaia", "description": "Residence DJERBA - 264 logements promotionnels", "created_at": datetime.now(timezone.utc).isoformat()})
        residence = await db.residences.find_one({"_id": result.inserted_id})
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from seed_edimco import ALL_LOTS, PRIX_M2
    rid = str(residence["_id"])
    docs = []
    for lot in ALL_LOTS:
        docs.append({"residence_id": rid, "numero_lot": lot["lot"], "bloc": lot["bloc"], "etage": lot["etage"], "destination": lot["dest"], "type_appart": lot["type"], "surface_habitable": lot["sh"], "surface_utile": lot["su"], "prix": round(lot["sh"] * PRIX_M2), "statut": "disponible", "client_id": None, "created_at": datetime.now(timezone.utc).isoformat()})
    await db.appartements.insert_many(docs)
    await manager.broadcast({"type": "appartement_created"})
    return {"message": f"{len(docs)} lots EDIMCO crees", "seeded": True, "count": len(docs)}
