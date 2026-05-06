from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from core.database import db, SOFT_DELETE_FILTER
from core.auth import get_current_user
from core.permissions import require_role, get_permissions
from core.websocket import manager
from core.helpers import audit_log
from models.schemas import AppartementCreate, AppartementUpdate, ResidenceCreate, ResidenceUpdate

router = APIRouter(tags=["apartments"])


@router.get("/residences")
async def get_residences(current_user: dict = Depends(get_current_user)):
    result = []
    async for r in db.residences.find({}):
        result.append({"id": str(r["_id"]), "nom": r.get("nom", ""), "adresse": r.get("adresse", ""), "description": r.get("description", "")})
    return result

@router.post("/residences")
async def create_residence(residence: ResidenceCreate, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    residence_doc = {**residence.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    result = await db.residences.insert_one(residence_doc)
    await manager.broadcast({"type": "residence_created", "data": {"id": str(result.inserted_id)}})
    return {"id": str(result.inserted_id), **residence.model_dump()}

@router.put("/residences/{residence_id}")
async def update_residence(residence_id: str, residence: ResidenceUpdate, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    update_data = {k: v for k, v in residence.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnee")
    result = await db.residences.update_one({"_id": ObjectId(residence_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Residence non trouvee")
    await manager.broadcast({"type": "residence_updated", "data": {"id": residence_id}})
    return {"id": residence_id, **update_data}

@router.delete("/residences/{residence_id}")
async def delete_residence(residence_id: str, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    result = await db.residences.delete_one({"_id": ObjectId(residence_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Residence non trouvee")
    await manager.broadcast({"type": "residence_deleted", "data": {"id": residence_id}})
    return {"message": "Residence supprimee"}


@router.get("/appartements")
async def get_appartements(current_user: dict = Depends(get_current_user)):
    result = []
    async for a in db.appartements.find(SOFT_DELETE_FILTER):
        result.append({
            "id": str(a["_id"]), "residence_id": a.get("residence_id", ""),
            "type_appart": a.get("type_appart", ""), "prix": a.get("prix", 0),
            "etage": a.get("etage", ""), "statut": a.get("statut", "disponible"),
            "surface": a.get("surface"), "surface_habitable": a.get("surface_habitable"),
            "surface_utile": a.get("surface_utile"), "description": a.get("description", ""),
            "client_id": a.get("client_id"), "bloc": a.get("bloc", ""),
            "numero_lot": a.get("numero_lot", ""), "destination": a.get("destination", ""),
            "created_at": a.get("created_at", "")
        })
    return result

@router.post("/appartements")
async def create_appartement(appart: AppartementCreate, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    doc = {**appart.model_dump(), "client_id": None, "deleted_at": None, "created_at": datetime.now(timezone.utc).isoformat()}
    result = await db.appartements.insert_one(doc)
    await audit_log(current_user, "CREATE", "appartement", str(result.inserted_id), f"Lot {appart.numero_lot}", new_values=appart.model_dump())
    await manager.broadcast({"type": "appartement_created", "data": {"id": str(result.inserted_id)}})
    return {"id": str(result.inserted_id), **appart.model_dump()}

@router.put("/appartements/{appart_id}")
async def update_appartement(appart_id: str, appart: AppartementUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in appart.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnee")
    existing = await db.appartements.find_one({"_id": ObjectId(appart_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Appartement non trouve")
    old_vals = {k: existing.get(k) for k in update_data.keys() if existing.get(k) != update_data.get(k)}
    perms = get_permissions(current_user.get("role", "user"))
    if "prix" in update_data and update_data["prix"] != existing.get("prix"):
        if perms["needs_approval"]:
            from routes.admin import send_approval_notification_to_admins
            import asyncio
            approval_doc = {
                "requester_id": current_user["_id"],
                "requester_name": current_user.get("name", current_user.get("email", "")),
                "requester_role": current_user.get("role", "user"),
                "action": "modify_price", "entity_type": "appartement",
                "entity_id": appart_id, "entity_name": f"Lot {existing.get('numero_lot', '')} Bloc {existing.get('bloc', '')}",
                "details": {"old_prix": existing.get("prix"), "new_prix": update_data["prix"]},
                "status": "pending", "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.approval_requests.insert_one(approval_doc)
            await audit_log(current_user, "APPROVAL_REQUEST", "appartement", appart_id, f"Lot {existing.get('numero_lot', '')}", new_values={"action": "modify_price", "new_prix": update_data["prix"]})
            await manager.broadcast({"type": "approval_request_created"})
            asyncio.create_task(send_approval_notification_to_admins(approval_doc))
            return {"message": "Demande d'approbation envoyee", "approval_required": True}
    if appart.statut and appart.statut != existing.get("statut"):
        if appart.statut == "disponible" and existing.get("client_id"):
            update_data["client_id"] = None
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.appartements.update_one({"_id": ObjectId(appart_id)}, {"$set": update_data})
    await audit_log(current_user, "UPDATE", "appartement", appart_id, f"Lot {existing.get('numero_lot', '')} Bloc {existing.get('bloc', '')}", old_values=old_vals, new_values=update_data)
    await manager.broadcast({"type": "appartement_updated", "data": {"id": appart_id}})
    return {"id": appart_id, **update_data}

@router.delete("/appartements/{appart_id}")
async def delete_appartement(appart_id: str, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    existing = await db.appartements.find_one({"_id": ObjectId(appart_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Appartement non trouve")
    await db.appartements.update_one({"_id": ObjectId(appart_id)}, {"$set": {
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": current_user["_id"],
        "deleted_by_name": current_user.get("name", current_user.get("email", ""))
    }})
    await audit_log(current_user, "DELETE", "appartement", appart_id, f"Lot {existing.get('numero_lot', '')}")
    await manager.broadcast({"type": "appartement_deleted", "data": {"id": appart_id}})
    return {"message": "Appartement supprime"}


@router.get("/reservations")
async def get_reservations(current_user: dict = Depends(get_current_user)):
    result = []
    async for r in db.reservations.find({}).sort("date", -1).limit(100):
        result.append({
            "id": str(r["_id"]), "client_id": r.get("client_id", ""),
            "client_nom": r.get("client_nom", ""), "appartement_id": r.get("appartement_id", ""),
            "bloc": r.get("bloc", ""), "numero_lot": r.get("numero_lot", ""),
            "type_appart": r.get("type_appart", ""), "action": r.get("action", ""),
            "agent": r.get("agent", ""), "date": r.get("date", "")
        })
    return result
