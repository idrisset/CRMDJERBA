"""
DJERBA CONSTRUCTION CRM API - Modular Architecture
Main server file: app creation, middleware, routers, startup/shutdown
"""
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Core imports
from core.database import db, client as mongo_client, SOFT_DELETE_FILTER
from core.auth import hash_password, verify_password, get_current_user
from core.permissions import ROLES, get_permissions, require_role
from core.websocket import manager
from core.helpers import audit_log

# Route imports
from routes.auth import router as auth_router
from routes.clients import router as clients_router
from routes.apartments import router as apartments_router
from routes.prospects import router as prospects_router
from routes.dashboard import router as dashboard_router
from routes.admin import router as admin_router
from routes.whatsapp import router as whatsapp_router
from routes.backups import router as backups_router
from routes.exports import router as exports_router
from routes.trash import router as trash_router

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the app
app = FastAPI(title="DJERBA CONSTRUCTION CRM API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers under /api prefix
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(clients_router)
api_router.include_router(apartments_router)
api_router.include_router(prospects_router)
api_router.include_router(dashboard_router)
api_router.include_router(admin_router)
api_router.include_router(whatsapp_router)
api_router.include_router(backups_router)
api_router.include_router(exports_router)
api_router.include_router(trash_router)


@api_router.get("/")
async def root():
    return {"message": "DJERBA CONSTRUCTION CRM API", "version": "3.0"}


app.include_router(api_router)


# Health check (no auth)
@app.get("/api/health")
async def health_check():
    try:
        await db.command("ping")
        users_count = await db.users.count_documents({})
        clients_count = await db.clients.count_documents(SOFT_DELETE_FILTER)
        apparts_count = await db.appartements.count_documents(SOFT_DELETE_FILTER)
        return {"status": "ok", "database": "connected", "users": users_count, "clients": clients_count, "appartements": apparts_count}
    except Exception as e:
        return {"status": "error", "database": str(e)}


# Download endpoints
@app.get("/api/download-build")
async def download_build():
    zip_path = "/app/deploy/frontend-cpanel.zip"
    if os.path.exists(zip_path):
        return FileResponse(zip_path, filename="frontend-cpanel.zip", media_type="application/zip")
    return {"error": "Build not found"}

@app.get("/api/download-backend")
async def download_backend():
    zip_path = "/app/deploy/backend-vps.zip"
    if os.path.exists(zip_path):
        return FileResponse(zip_path, filename="backend-vps.zip", media_type="application/zip")
    return {"error": "Build not found"}

@app.get("/api/download-install-script")
async def download_install_script():
    path = "/app/deploy/install-vps.sh"
    if os.path.exists(path):
        return FileResponse(path, filename="install-vps.sh", media_type="text/plain")
    return {"error": "Not found"}


# WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({"type": "message", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Scheduler
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup_event():
    from datetime import datetime, timezone
    logger.info("=== STARTUP ===")
    logger.info(f"DB_NAME: {os.environ.get('DB_NAME')}")
    logger.info(f"MONGO_URL: {os.environ.get('MONGO_URL', '')[:40]}...")

    try:
        await db.command("ping")
        logger.info("MongoDB connection: OK")
    except Exception as e:
        logger.error(f"MongoDB connection FAILED: {e}")
        return

    # Indexes
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index([("email", 1), ("timestamp", -1)])
    await db.login_attempts.create_index([("email", 1), ("ip", 1), ("success", 1), ("timestamp", -1)])
    await db.login_attempts.create_index([("ip", 1), ("success", 1), ("timestamp", -1)])
    await db.banned_ips.create_index("ip", unique=True)
    await db.banned_ips.create_index("banned_until", expireAfterSeconds=0)

    # Admin user seed
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@immo.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email, "password_hash": hashed,
            "name": "Administrateur", "role": "super_admin",
            "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    else:
        if existing.get("role") == "admin":
            await db.users.update_one({"email": admin_email}, {"$set": {"role": "super_admin"}})
            logger.info(f"Migrated admin role to super_admin: {admin_email}")
        if not verify_password(admin_password, existing["password_hash"]):
            await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
            logger.info(f"Admin password updated: {admin_email}")

    # Seed EDIMCO residence
    try:
        if await db.residences.count_documents({}) == 0:
            await db.residences.insert_one({"nom": "EDIMCO", "adresse": "EDIMCO, Commune de Bejaia, Wilaya de Bejaia", "description": "Residence DJERBA - 264 logements promotionnels", "created_at": datetime.now(timezone.utc).isoformat()})
            logger.info("EDIMCO residence created")
    except Exception as e:
        logger.error(f"Residence seed error: {e}")

    # Seed apartments
    try:
        if await db.appartements.count_documents({}) == 0:
            logger.info("No apartments found - seeding EDIMCO lots...")
            residence = await db.residences.find_one({"nom": "EDIMCO"})
            if residence:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from seed_edimco import ALL_LOTS, PRIX_M2
                rid = str(residence["_id"])
                docs = []
                for lot in ALL_LOTS:
                    docs.append({
                        "residence_id": rid, "numero_lot": lot["lot"], "bloc": lot["bloc"],
                        "etage": lot["etage"], "destination": lot["dest"], "type_appart": lot["type"],
                        "surface_habitable": lot["sh"], "surface_utile": lot["su"],
                        "prix": round(lot["sh"] * PRIX_M2), "statut": "disponible",
                        "client_id": None, "created_at": datetime.now(timezone.utc).isoformat()
                    })
                await db.appartements.insert_many(docs)
                logger.info(f"Seeded {len(docs)} EDIMCO lots")
    except Exception as e:
        logger.error(f"Apartments seed error: {e}")

    # Test credentials file
    try:
        os.makedirs("/app/memory", exist_ok=True)
        with open("/app/memory/test_credentials.md", "w") as f:
            f.write(f"# Test Credentials\n\n## Admin Account\n- Email: {admin_email}\n- Password: {admin_password}\n- Role: super_admin\n")
    except Exception:
        pass

    # Data migrations
    try:
        last_ref = await db.clients.find_one({"reference": {"$exists": True, "$ne": "", "$ne": None}}, sort=[("reference", -1)])
        counter = 0
        if last_ref and last_ref.get("reference"):
            try:
                counter = int(last_ref["reference"].replace("#", ""))
            except (ValueError, TypeError):
                counter = 0
        clients_without_ref = db.clients.find({"$or": [{"reference": {"$exists": False}}, {"reference": None}, {"reference": ""}]}).sort("created_at", 1)
        async for c in clients_without_ref:
            counter += 1
            await db.clients.update_one({"_id": c["_id"]}, {"$set": {"reference": f"#{counter:03d}"}})
        if counter > 0:
            logger.info(f"Migration: assigned references up to #{counter:03d}")
    except Exception as e:
        logger.error(f"Reference migration error: {e}")

    try:
        migrated = 0
        async for c in db.clients.find({"appartement_id": {"$exists": True, "$ne": None}, "appartement_ids": {"$exists": False}}):
            old_id = c.get("appartement_id")
            if old_id:
                await db.clients.update_one({"_id": c["_id"]}, {"$set": {"appartement_ids": [old_id]}})
                migrated += 1
        if migrated > 0:
            logger.info(f"Migration: migrated {migrated} clients from appartement_id to appartement_ids")
    except Exception as e:
        logger.error(f"Apartment migration error: {e}")

    try:
        result = await db.users.update_many({"role": "admin"}, {"$set": {"role": "super_admin"}})
        if result.modified_count > 0:
            logger.info(f"Migration: migrated {result.modified_count} admin users to super_admin")
    except Exception as e:
        logger.error(f"Role migration error: {e}")

    # Start backup scheduler
    try:
        from routes.backups import scheduled_backup_6h, scheduled_backup_daily, scheduled_weekly_email_export
        scheduler.add_job(scheduled_backup_6h, 'interval', hours=6, id='backup_6h', replace_existing=True)
        scheduler.add_job(scheduled_backup_daily, 'cron', hour=2, minute=0, id='backup_daily', replace_existing=True)
        scheduler.add_job(scheduled_weekly_email_export, 'cron', day_of_week='sun', hour=3, minute=0, id='weekly_email_export', replace_existing=True)
        scheduler.start()
        logger.info("Backup scheduler started (every 6h + daily at 02:00)")
    except Exception as e:
        logger.error(f"Scheduler start error: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        pass
    mongo_client.close()
