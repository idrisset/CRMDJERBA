from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from core.database import db, SOFT_DELETE_FILTER
from core.auth import get_current_user
from core.permissions import get_permissions
from core.websocket import manager
from core.helpers import audit_log, generate_client_reference, check_duplicate_client, send_notification_email
from models.schemas import ClientCreate, ClientUpdate
import asyncio
import os

router = APIRouter(tags=["clients"])


@router.get("/clients")
async def get_clients(current_user: dict = Depends(get_current_user)):
    result = []
    async for c in db.clients.find(SOFT_DELETE_FILTER):
        appart_ids = c.get("appartement_ids") or []
        if not appart_ids and c.get("appartement_id"):
            appart_ids = [c["appartement_id"]]
        appartements_info = []
        for aid in appart_ids:
            try:
                a = await db.appartements.find_one({"_id": ObjectId(aid)})
                if a:
                    appartements_info.append({
                        "id": str(a["_id"]),
                        "numero_lot": a.get("numero_lot", ""),
                        "bloc": a.get("bloc", ""),
                        "type_appart": a.get("type_appart", ""),
                        "statut": a.get("statut", ""),
                    })
            except Exception:
                pass
        client_data = {
            "id": str(c["_id"]),
            "reference": c.get("reference", ""),
            "nom": c.get("nom", ""),
            "telephone": c.get("telephone", ""),
            "telephone2": c.get("telephone2", ""),
            "email": c.get("email", ""),
            "salaire": c.get("salaire"),
            "budget_min": c.get("budget_min"),
            "budget_max": c.get("budget_max"),
            "objectif": c.get("objectif", ""),
            "mode_paiement": c.get("mode_paiement", ""),
            "etage_souhaite": c.get("etage_souhaite", ""),
            "situation_familiale": c.get("situation_familiale", ""),
            "notes": c.get("notes", ""),
            "statut": c.get("statut", "nouveau"),
            "appartement_ids": appart_ids,
            "appartements_info": appartements_info,
            "source": c.get("source", "manual"),
            "created_at": c.get("created_at", ""),
            "created_by": c.get("created_by", "")
        }
        result.append(client_data)
    return result


@router.post("/clients/check-duplicates")
async def check_duplicates(client: ClientCreate, current_user: dict = Depends(get_current_user)):
    duplicates = await check_duplicate_client(client.nom, client.telephone, client.email)
    return {"duplicates": duplicates, "has_duplicates": len(duplicates) > 0}


@router.post("/clients")
async def create_client(client: ClientCreate, current_user: dict = Depends(get_current_user)):
    client_data = client.model_dump()
    appartement_ids = client_data.pop("appartement_ids", None) or []
    force_create = client_data.pop("force_create", False)
    if not force_create:
        duplicates = await check_duplicate_client(client.nom, client.telephone, client.email)
        if duplicates:
            return {"id": None, "duplicates": duplicates, "needs_confirmation": True}
    reference = await generate_client_reference()
    client_doc = {
        **client_data,
        "reference": reference,
        "appartement_ids": appartement_ids,
        "source": "manual",
        "deleted_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["_id"]
    }
    result = await db.clients.insert_one(client_doc)
    client_id = str(result.inserted_id)
    await audit_log(current_user, "CREATE", "client", client_id, client_data.get("nom", ""), new_values=client_data)
    for appart_id in appartement_ids:
        if appart_id:
            try:
                appart = await db.appartements.find_one({"_id": ObjectId(appart_id)})
                if appart and appart.get("statut") == "disponible":
                    await db.appartements.update_one({"_id": ObjectId(appart_id)}, {"$set": {"statut": "reserve", "client_id": client_id}})
                    await db.reservations.insert_one({
                        "client_id": client_id, "client_nom": client_data.get("nom", ""),
                        "appartement_id": appart_id, "bloc": appart.get("bloc", ""),
                        "numero_lot": appart.get("numero_lot", ""), "type_appart": appart.get("type_appart", ""),
                        "action": "reserve", "agent": current_user.get("name", current_user.get("email", "")),
                        "date": datetime.now(timezone.utc).isoformat()
                    })
                    await manager.broadcast({"type": "appartement_updated", "data": {"id": appart_id}})
            except Exception:
                pass
    await manager.broadcast({"type": "client_created", "data": {"id": client_id}})
    return {"id": client_id, "reference": reference, **client_data}


@router.put("/clients/{client_id}")
async def update_client(client_id: str, client: ClientUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in client.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnee a mettre a jour")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user["_id"]
    existing = await db.clients.find_one({"_id": ObjectId(client_id), **SOFT_DELETE_FILTER})
    if not existing:
        raise HTTPException(status_code=404, detail="Client non trouve")
    old_vals = {k: existing.get(k) for k in update_data.keys() if existing.get(k) != update_data.get(k)}
    new_appart_ids = update_data.get("appartement_ids")
    old_appart_ids = existing.get("appartement_ids") or []
    if not old_appart_ids and existing.get("appartement_id"):
        old_appart_ids = [existing["appartement_id"]]
    if new_appart_ids is not None:
        old_set = set(old_appart_ids)
        new_set = set([a for a in new_appart_ids if a and a != "none"])
        for aid in old_set - new_set:
            try:
                await db.appartements.update_one({"_id": ObjectId(aid)}, {"$set": {"statut": "disponible", "client_id": None}})
                old_a = await db.appartements.find_one({"_id": ObjectId(aid)})
                await db.reservations.insert_one({
                    "client_id": client_id, "client_nom": existing.get("nom", ""),
                    "appartement_id": aid, "bloc": old_a.get("bloc", "") if old_a else "",
                    "numero_lot": old_a.get("numero_lot", "") if old_a else "",
                    "action": "libere", "agent": current_user.get("name", current_user.get("email", "")),
                    "date": datetime.now(timezone.utc).isoformat()
                })
                await manager.broadcast({"type": "appartement_updated", "data": {"id": aid}})
            except Exception:
                pass
        for aid in new_set - old_set:
            try:
                appart = await db.appartements.find_one({"_id": ObjectId(aid)})
                if appart:
                    if appart.get("statut") != "disponible" and appart.get("client_id") and appart.get("client_id") != client_id:
                        raise HTTPException(status_code=409, detail=f"Lot {appart.get('numero_lot')} deja reserve")
                    await db.appartements.update_one({"_id": ObjectId(aid)}, {"$set": {"statut": "reserve", "client_id": client_id}})
                    await db.reservations.insert_one({
                        "client_id": client_id, "client_nom": update_data.get("nom", existing.get("nom", "")),
                        "appartement_id": aid, "bloc": appart.get("bloc", ""),
                        "numero_lot": appart.get("numero_lot", ""), "type_appart": appart.get("type_appart", ""),
                        "action": "reserve", "agent": current_user.get("name", current_user.get("email", "")),
                        "date": datetime.now(timezone.utc).isoformat()
                    })
                    await manager.broadcast({"type": "appartement_updated", "data": {"id": aid}})
            except HTTPException:
                raise
            except Exception:
                pass
        update_data["appartement_ids"] = list(new_set)
    if client.statut == "vendu":
        final_ids = update_data.get("appartement_ids", old_appart_ids)
        for aid in final_ids:
            try:
                await db.appartements.update_one({"_id": ObjectId(aid)}, {"$set": {"statut": "vendu"}})
                appart = await db.appartements.find_one({"_id": ObjectId(aid)})
                await db.reservations.insert_one({
                    "client_id": client_id, "client_nom": update_data.get("nom", existing.get("nom", "")),
                    "appartement_id": aid, "bloc": appart.get("bloc", "") if appart else "",
                    "numero_lot": appart.get("numero_lot", "") if appart else "",
                    "action": "vendu", "agent": current_user.get("name", current_user.get("email", "")),
                    "date": datetime.now(timezone.utc).isoformat()
                })
                await manager.broadcast({"type": "appartement_updated", "data": {"id": aid}})
            except Exception:
                pass
    await db.clients.update_one({"_id": ObjectId(client_id)}, {"$set": update_data})
    await manager.broadcast({"type": "client_updated", "data": {"id": client_id}})
    await audit_log(current_user, "UPDATE", "client", client_id, existing.get("nom", ""), old_values=old_vals, new_values=update_data)
    return {"id": client_id, **update_data}


@router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
    from routes.admin import send_approval_notification_to_admins
    perms = get_permissions(current_user.get("role", "user"))
    existing = await db.clients.find_one({"_id": ObjectId(client_id), **SOFT_DELETE_FILTER})
    if not existing:
        raise HTTPException(status_code=404, detail="Client non trouve")
    if perms["needs_approval"]:
        approval_doc = {
            "requester_id": current_user["_id"],
            "requester_name": current_user.get("name", current_user.get("email", "")),
            "requester_role": current_user.get("role", "user"),
            "action": "delete_client", "entity_type": "client",
            "entity_id": client_id, "entity_name": existing.get("nom", ""),
            "details": {"reference": existing.get("reference", ""), "telephone": existing.get("telephone", "")},
            "status": "pending", "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.approval_requests.insert_one(approval_doc)
        await audit_log(current_user, "APPROVAL_REQUEST", "client", client_id, existing.get("nom", ""), new_values={"action": "delete_client"})
        await manager.broadcast({"type": "approval_request_created"})
        asyncio.create_task(send_approval_notification_to_admins(approval_doc))
        return {"message": "Demande d'approbation envoyee au Super Administrateur", "approval_required": True}
    appart_ids = existing.get("appartement_ids") or []
    if not appart_ids and existing.get("appartement_id"):
        appart_ids = [existing["appartement_id"]]
    for aid in appart_ids:
        try:
            await db.appartements.update_one({"_id": ObjectId(aid)}, {"$set": {"statut": "disponible", "client_id": None}})
            await manager.broadcast({"type": "appartement_updated", "data": {"id": aid}})
        except Exception:
            pass
    await db.clients.update_one({"_id": ObjectId(client_id)}, {"$set": {
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": current_user["_id"],
        "deleted_by_name": current_user.get("name", current_user.get("email", ""))
    }})
    await audit_log(current_user, "DELETE", "client", client_id, existing.get("nom", ""))
    await manager.broadcast({"type": "client_deleted", "data": {"id": client_id}})
    return {"message": "Client deplace dans la corbeille"}


# ============ DUPLICATE CLIENTS ============
@router.get("/clients/duplicates")
async def get_duplicate_clients(current_user: dict = Depends(get_current_user)):
    pipeline = [
        {"$match": SOFT_DELETE_FILTER},
        {"$group": {"_id": "$telephone", "count": {"$sum": 1}, "clients": {"$push": {"id": {"$toString": "$_id"}, "nom": "$nom", "telephone": "$telephone", "email": "$email", "reference": "$reference", "created_at": "$created_at"}}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]
    tel_dupes = []
    async for group in db.clients.aggregate(pipeline):
        tel_dupes.append({"type": "telephone", "value": group["_id"], "clients": group["clients"]})
    pipeline_email = [
        {"$match": {**SOFT_DELETE_FILTER, "email": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": {"$toLower": "$email"}, "count": {"$sum": 1}, "clients": {"$push": {"id": {"$toString": "$_id"}, "nom": "$nom", "telephone": "$telephone", "email": "$email", "reference": "$reference", "created_at": "$created_at"}}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]
    email_dupes = []
    async for group in db.clients.aggregate(pipeline_email):
        email_dupes.append({"type": "email", "value": group["_id"], "clients": group["clients"]})
    pipeline_nom = [
        {"$match": SOFT_DELETE_FILTER},
        {"$group": {"_id": {"$toLower": "$nom"}, "count": {"$sum": 1}, "clients": {"$push": {"id": {"$toString": "$_id"}, "nom": "$nom", "telephone": "$telephone", "email": "$email", "reference": "$reference", "created_at": "$created_at"}}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]
    nom_dupes = []
    async for group in db.clients.aggregate(pipeline_nom):
        nom_dupes.append({"type": "nom", "value": group["_id"], "clients": group["clients"]})
    return {"telephone_duplicates": tel_dupes, "email_duplicates": email_dupes, "nom_duplicates": nom_dupes,
            "total_groups": len(tel_dupes) + len(email_dupes) + len(nom_dupes)}


@router.post("/clients/merge/{keep_id}/{merge_id}")
async def merge_clients_action(keep_id: str, merge_id: str, current_user: dict = Depends(get_current_user)):
    from core.permissions import require_role
    require_role(current_user, min_level=2)
    keep = await db.clients.find_one({"_id": ObjectId(keep_id), **SOFT_DELETE_FILTER})
    merge = await db.clients.find_one({"_id": ObjectId(merge_id), **SOFT_DELETE_FILTER})
    if not keep or not merge:
        raise HTTPException(status_code=404, detail="Client non trouve")
    merge_fields = {}
    for field in ["telephone2", "email", "adresse", "salaire", "situation_familiale", "notes", "source"]:
        if not keep.get(field) and merge.get(field):
            merge_fields[field] = merge[field]
    if merge.get("notes") and keep.get("notes"):
        merge_fields["notes"] = f"{keep['notes']}\n---\n[Fusionne] {merge['notes']}"
    keep_apparts = keep.get("appartement_ids") or []
    merge_apparts = merge.get("appartement_ids") or []
    if not merge_apparts and merge.get("appartement_id"):
        merge_apparts = [merge["appartement_id"]]
    combined = list(set(keep_apparts + merge_apparts))
    merge_fields["appartement_ids"] = combined
    merge_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    if merge_fields:
        await db.clients.update_one({"_id": ObjectId(keep_id)}, {"$set": merge_fields})
    for aid in merge_apparts:
        try:
            await db.appartements.update_one({"_id": ObjectId(aid), "client_id": merge_id}, {"$set": {"client_id": keep_id}})
        except Exception:
            pass
    await db.clients.update_one({"_id": ObjectId(merge_id)}, {"$set": {
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": current_user["_id"],
        "deleted_by_name": f"FUSION -> {keep.get('reference', keep_id)}"
    }})
    await audit_log(current_user, "MERGE", "client", keep_id, keep.get("nom", ""),
                    old_values={"merged_from": merge_id, "merged_name": merge.get("nom", "")},
                    new_values=merge_fields)
    await manager.broadcast({"type": "client_updated", "data": {"id": keep_id}})
    return {"message": f"Clients fusionnes. {merge.get('nom', '')} -> {keep.get('nom', '')}", "kept_id": keep_id}
