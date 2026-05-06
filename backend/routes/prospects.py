from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from core.database import db, SOFT_DELETE_FILTER
from core.auth import get_current_user
from core.helpers import audit_log
from core.websocket import manager
from models.schemas import ProspectCreate, ProspectUpdate

router = APIRouter(tags=["prospects"])


@router.get("/prospects")
async def get_prospects(current_user: dict = Depends(get_current_user)):
    result = []
    async for p in db.prospects.find(SOFT_DELETE_FILTER).sort("created_at", -1):
        result.append({
            "id": str(p["_id"]), "nom": p.get("nom", ""), "telephone": p.get("telephone", ""),
            "telephone2": p.get("telephone2", ""), "email": p.get("email", ""),
            "ville": p.get("ville", ""), "quartier": p.get("quartier", ""),
            "type_logement": p.get("type_logement", ""), "etage_souhaite": p.get("etage_souhaite", ""),
            "nombre_pieces": p.get("nombre_pieces"), "budget_min": p.get("budget_min"),
            "budget_max": p.get("budget_max"), "mode_paiement": p.get("mode_paiement", ""),
            "objectif": p.get("objectif", ""), "situation_familiale": p.get("situation_familiale", ""),
            "notes": p.get("notes", ""), "source": p.get("source", "foire"),
            "created_at": p.get("created_at", ""),
        })
    return result

@router.post("/prospects")
async def create_prospect(prospect: ProspectCreate, current_user: dict = Depends(get_current_user)):
    doc = {**prospect.model_dump(), "deleted_at": None, "created_at": datetime.now(timezone.utc).isoformat(), "created_by": current_user["_id"]}
    result = await db.prospects.insert_one(doc)
    await audit_log(current_user, "CREATE", "prospect", str(result.inserted_id), prospect.nom, new_values=prospect.model_dump())
    await manager.broadcast({"type": "prospect_created", "data": {"id": str(result.inserted_id)}})
    return {"id": str(result.inserted_id), **prospect.model_dump()}

@router.put("/prospects/{prospect_id}")
async def update_prospect(prospect_id: str, prospect: ProspectUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in prospect.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnee")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    existing_p = await db.prospects.find_one({"_id": ObjectId(prospect_id), **SOFT_DELETE_FILTER})
    if not existing_p:
        raise HTTPException(status_code=404, detail="Prospect non trouve")
    old_vals = {k: existing_p.get(k) for k in update_data.keys() if existing_p.get(k) != update_data.get(k)}
    await db.prospects.update_one({"_id": ObjectId(prospect_id)}, {"$set": update_data})
    await audit_log(current_user, "UPDATE", "prospect", prospect_id, existing_p.get("nom", ""), old_values=old_vals, new_values=update_data)
    await manager.broadcast({"type": "prospect_updated", "data": {"id": prospect_id}})
    return {"id": prospect_id, **update_data}

@router.delete("/prospects/{prospect_id}")
async def delete_prospect(prospect_id: str, current_user: dict = Depends(get_current_user)):
    existing = await db.prospects.find_one({"_id": ObjectId(prospect_id), **SOFT_DELETE_FILTER})
    if not existing:
        raise HTTPException(status_code=404, detail="Prospect non trouve")
    await db.prospects.update_one({"_id": ObjectId(prospect_id)}, {"$set": {
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": current_user["_id"],
        "deleted_by_name": current_user.get("name", current_user.get("email", ""))
    }})
    await audit_log(current_user, "DELETE", "prospect", prospect_id, existing.get("nom", ""))
    await manager.broadcast({"type": "prospect_deleted", "data": {"id": prospect_id}})
    return {"message": "Prospect deplace dans la corbeille"}

@router.get("/prospects/analytics")
async def get_prospects_analytics(current_user: dict = Depends(get_current_user)):
    total = await db.prospects.count_documents(SOFT_DELETE_FILTER)
    villes_pipeline = [{"$match": {"ville": {"$ne": None, "$ne": ""}, "deleted_at": None}}, {"$group": {"_id": "$ville", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
    villes = [{"name": v["_id"], "count": v["count"]} async for v in db.prospects.aggregate(villes_pipeline)]
    quartiers_pipeline = [{"$match": {"quartier": {"$ne": None, "$ne": ""}}}, {"$group": {"_id": "$quartier", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
    quartiers = [{"name": q["_id"], "count": q["count"]} async for q in db.prospects.aggregate(quartiers_pipeline)]
    types_pipeline = [{"$match": {"type_logement": {"$ne": None, "$ne": ""}}}, {"$group": {"_id": "$type_logement", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    types = [{"name": t["_id"], "count": t["count"]} async for t in db.prospects.aggregate(types_pipeline)]
    objectifs_pipeline = [{"$match": {"objectif": {"$ne": None, "$ne": ""}}}, {"$group": {"_id": "$objectif", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    objectifs = [{"name": o["_id"], "count": o["count"]} async for o in db.prospects.aggregate(objectifs_pipeline)]
    budget_pipeline = [{"$match": {"budget_max": {"$ne": None, "$gt": 0}}}, {"$group": {"_id": None, "avg_min": {"$avg": "$budget_min"}, "avg_max": {"$avg": "$budget_max"}}}]
    budget_avg = {"avg_min": 0, "avg_max": 0}
    async for b in db.prospects.aggregate(budget_pipeline):
        budget_avg = {"avg_min": b.get("avg_min", 0) or 0, "avg_max": b.get("avg_max", 0) or 0}
    paiement_pipeline = [{"$match": {"mode_paiement": {"$ne": None, "$ne": ""}}}, {"$group": {"_id": "$mode_paiement", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    paiements = [{"name": p["_id"], "count": p["count"]} async for p in db.prospects.aggregate(paiement_pipeline)]
    zone_pipeline = [{"$match": {"ville": {"$ne": None, "$ne": ""}, "quartier": {"$ne": None, "$ne": ""}}}, {"$group": {"_id": {"ville": "$ville", "quartier": "$quartier"}, "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 15}]
    zones = [{"ville": z["_id"]["ville"], "quartier": z["_id"]["quartier"], "count": z["count"]} async for z in db.prospects.aggregate(zone_pipeline)]
    return {"total": total, "top_villes": villes, "top_quartiers": quartiers, "top_types": types, "objectifs": objectifs, "budget_avg": budget_avg, "modes_paiement": paiements, "top_zones": zones}
