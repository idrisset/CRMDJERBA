from fastapi import APIRouter, Depends
from core.database import db, SOFT_DELETE_FILTER
from core.auth import get_current_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    total_clients = await db.clients.count_documents(SOFT_DELETE_FILTER)
    apparts_disponibles = await db.appartements.count_documents({"statut": "disponible", **SOFT_DELETE_FILTER})
    apparts_reserves = await db.appartements.count_documents({"statut": "reserve", **SOFT_DELETE_FILTER}) + await db.appartements.count_documents({"statut": "\u00e9serv\u00e9", **SOFT_DELETE_FILTER})
    apparts_vendus = await db.appartements.count_documents({"statut": "vendu", **SOFT_DELETE_FILTER})
    clients_nouveau = await db.clients.count_documents({"statut": "nouveau", **SOFT_DELETE_FILTER})
    clients_interesse = await db.clients.count_documents({"statut": "int\u00e9ress\u00e9", **SOFT_DELETE_FILTER})
    clients_visite = await db.clients.count_documents({"statut": "visite", **SOFT_DELETE_FILTER})
    clients_reserve = await db.clients.count_documents({"statut": "r\u00e9serv\u00e9", **SOFT_DELETE_FILTER})
    clients_vendu = await db.clients.count_documents({"statut": "vendu", **SOFT_DELETE_FILTER})
    clients_chaud = await db.clients.count_documents({"temperature": "chaud", **SOFT_DELETE_FILTER})
    clients_tiede = await db.clients.count_documents({"temperature": "ti\u00e8de", **SOFT_DELETE_FILTER})
    clients_froid = await db.clients.count_documents({"temperature": "froid", **SOFT_DELETE_FILTER})
    whatsapp_leads = await db.clients.count_documents({"source": "whatsapp", **SOFT_DELETE_FILTER})
    recent_clients = []
    async for c in db.clients.find(SOFT_DELETE_FILTER).sort("created_at", -1).limit(5):
        recent_clients.append({
            "id": str(c["_id"]), "nom": c.get("nom", ""), "statut": c.get("statut", ""),
            "temperature": c.get("temperature", "froid"), "source": c.get("source", "manual"),
            "created_at": c.get("created_at", "")
        })
    total_logements = await db.appartements.count_documents({"destination": "Logement"})
    logements_disponibles = await db.appartements.count_documents({"destination": "Logement", "statut": "disponible"})
    logements_reserves = await db.appartements.count_documents({"destination": "Logement", "statut": "r\u00e9serv\u00e9"})
    logements_vendus = await db.appartements.count_documents({"destination": "Logement", "statut": "vendu"})
    blocs_stats = {}
    for bloc in ["A", "B", "C", "D", "E", "F", "G", "H"]:
        blocs_stats[bloc] = {
            "total": await db.appartements.count_documents({"bloc": bloc, "destination": "Logement"}),
            "disponible": await db.appartements.count_documents({"bloc": bloc, "destination": "Logement", "statut": "disponible"}),
            "reserve": await db.appartements.count_documents({"bloc": bloc, "destination": "Logement", "statut": "r\u00e9serv\u00e9"}),
            "vendu": await db.appartements.count_documents({"bloc": bloc, "destination": "Logement", "statut": "vendu"}),
        }
    return {
        "total_clients": total_clients,
        "total_logements": total_logements, "logements_disponibles": logements_disponibles,
        "logements_reserves": logements_reserves, "logements_vendus": logements_vendus,
        "appartements_disponibles": apparts_disponibles, "appartements_reserves": apparts_reserves,
        "appartements_vendus": apparts_vendus,
        "clients_par_statut": {"nouveau": clients_nouveau, "int\u00e9ress\u00e9": clients_interesse, "visite": clients_visite, "r\u00e9serv\u00e9": clients_reserve, "vendu": clients_vendu},
        "clients_par_temperature": {"chaud": clients_chaud, "ti\u00e8de": clients_tiede, "froid": clients_froid},
        "whatsapp_leads": whatsapp_leads, "recent_clients": recent_clients, "blocs_stats": blocs_stats
    }
