"""Trash/Corbeille routes"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from core.database import db
from core.auth import get_current_user
from core.permissions import require_role
from core.websocket import manager
from core.helpers import audit_log

router = APIRouter(prefix="/trash", tags=["trash"])


@router.get("")
async def get_trash(current_user: dict = Depends(get_current_user)):
    result = []
    async for c in db.clients.find({"deleted_at": {"$ne": None}}).sort("deleted_at", -1):
        result.append({"id": str(c["_id"]), "entity_type": "client", "entity_name": c.get("nom", ""), "deleted_at": c.get("deleted_at", ""), "deleted_by": c.get("deleted_by", ""), "deleted_by_name": c.get("deleted_by_name", ""), "data": {k: v for k, v in c.items() if k not in ("_id", "deleted_at", "deleted_by", "deleted_by_name")}})
    async for p in db.prospects.find({"deleted_at": {"$ne": None}}).sort("deleted_at", -1):
        result.append({"id": str(p["_id"]), "entity_type": "prospect", "entity_name": p.get("nom", ""), "deleted_at": p.get("deleted_at", ""), "deleted_by": p.get("deleted_by", ""), "deleted_by_name": p.get("deleted_by_name", ""), "data": {k: v for k, v in p.items() if k not in ("_id", "deleted_at", "deleted_by", "deleted_by_name")}})
    async for a in db.appartements.find({"deleted_at": {"$ne": None}}).sort("deleted_at", -1):
        result.append({"id": str(a["_id"]), "entity_type": "appartement", "entity_name": f"Lot {a.get('numero_lot', '')} Bloc {a.get('bloc', '')}", "deleted_at": a.get("deleted_at", ""), "deleted_by": a.get("deleted_by", ""), "deleted_by_name": a.get("deleted_by_name", ""), "data": {k: v for k, v in a.items() if k not in ("_id", "deleted_at", "deleted_by", "deleted_by_name")}})
    result.sort(key=lambda x: x.get("deleted_at", ""), reverse=True)
    return result

@router.post("/{entity_type}/{entity_id}/restore")
async def restore_from_trash(entity_type: str, entity_id: str, current_user: dict = Depends(get_current_user)):
    collection_map = {"client": "clients", "prospect": "prospects", "appartement": "appartements"}
    collection_name = collection_map.get(entity_type)
    if not collection_name:
        raise HTTPException(status_code=400, detail="Type invalide")
    collection = db[collection_name]
    existing = await collection.find_one({"_id": ObjectId(entity_id), "deleted_at": {"$ne": None}})
    if not existing:
        raise HTTPException(status_code=404, detail="Element non trouve dans la corbeille")
    await collection.update_one({"_id": ObjectId(entity_id)}, {"$set": {"deleted_at": None, "deleted_by": None, "deleted_by_name": None}})
    await audit_log(current_user, "RESTORE", entity_type, entity_id, existing.get("nom", existing.get("numero_lot", "")))
    await manager.broadcast({"type": f"{entity_type}_restored", "data": {"id": entity_id}})
    return {"message": "Element restaure"}

@router.delete("/{entity_type}/{entity_id}/permanent")
async def permanent_delete(entity_type: str, entity_id: str, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    collection_map = {"client": "clients", "prospect": "prospects", "appartement": "appartements"}
    collection_name = collection_map.get(entity_type)
    if not collection_name:
        raise HTTPException(status_code=400, detail="Type invalide")
    collection = db[collection_name]
    existing = await collection.find_one({"_id": ObjectId(entity_id), "deleted_at": {"$ne": None}})
    if not existing:
        raise HTTPException(status_code=404, detail="Element non trouve")
    await collection.delete_one({"_id": ObjectId(entity_id)})
    await audit_log(current_user, "PERMANENT_DELETE", entity_type, entity_id, existing.get("nom", existing.get("numero_lot", "")))
    return {"message": "Element supprime definitivement"}
