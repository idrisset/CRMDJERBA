"""Backup & Restore routes + scheduler functions"""
import os
import io
import asyncio
import logging
import zipfile
import base64
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import resend
from core.database import db
from core.auth import get_current_user
from core.permissions import require_role
from core.helpers import SENDER_EMAIL
import backup_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backups", tags=["backups"])


@router.get("")
async def get_backups(current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    result = []
    async for b in db.backups.find({}, {"_id": 0}).sort("timestamp", -1).limit(50):
        result.append(b)
    return result

@router.post("")
async def create_backup_endpoint(current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    try:
        result = await backup_manager.create_backup(backup_type="manual", triggered_by=current_user.get("name", current_user.get("email", "")))
        result_db = {k: v for k, v in result.items() if k != "_id"}
        await db.backups.insert_one(result_db)
        if result["status"] == "success":
            await send_backup_alert_email("success", result)
        return result_db
    except Exception as e:
        logger.error(f"Backup creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{backup_id}/restore")
async def restore_backup_endpoint(backup_id: str, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    try:
        safety = await backup_manager.create_backup(backup_type="pre_restore_safety", triggered_by="System")
        safety_db = {k: v for k, v in safety.items() if k != "_id"}
        await db.backups.insert_one(safety_db)
        result = await backup_manager.restore_backup(backup_id)
        if result["status"] == "success":
            await send_backup_alert_email("restored", result)
        return result
    except Exception as e:
        logger.error(f"Restore error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{backup_id}")
async def delete_backup_endpoint(backup_id: str, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    try:
        result = await backup_manager.delete_backup(backup_id)
        await db.backups.delete_one({"backup_id": backup_id})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{backup_id}/download")
async def download_backup(backup_id: str, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    try:
        backup_path = backup_manager.get_backup_path(backup_id)
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Backup non trouve")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for dirpath, dirnames, filenames in os.walk(backup_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    arcname = os.path.relpath(filepath, backup_path)
                    zf.write(filepath, arcname)
        zip_buffer.seek(0)
        return StreamingResponse(zip_buffer, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=backup_{backup_id}.zip"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email-settings")
async def get_backup_email_settings(current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    settings = await db.notification_settings.find_one({"type": "backup_email_export"})
    if not settings:
        return {"enabled": False, "email": os.environ.get("NOTIFICATION_EMAIL", ""), "schedule": "weekly"}
    return {"enabled": settings.get("enabled", False), "email": settings.get("email", ""), "schedule": "weekly"}

class BackupEmailSettings(BaseModel):
    enabled: bool
    email: str = ""

@router.post("/email-settings")
async def save_backup_email_settings(settings: BackupEmailSettings, current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    await db.notification_settings.update_one({"type": "backup_email_export"}, {"$set": {"type": "backup_email_export", "enabled": settings.enabled, "email": settings.email, "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    return {"message": "Parametres sauvegardes"}

@router.post("/send-test-email")
async def send_test_backup_email(current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=3)
    settings = await db.notification_settings.find_one({"type": "backup_email_export"})
    recipient = (settings.get("email") if settings else None) or os.environ.get("NOTIFICATION_EMAIL", "")
    if not recipient or not resend.api_key:
        raise HTTPException(status_code=400, detail="Email ou cle API non configure")
    html = "<div style='font-family:Arial;padding:20px;'><h2>Test - Export Backup CRM</h2><p>Ceci est un email de test. L'export hebdomadaire fonctionne.</p></div>"
    params = {"from": SENDER_EMAIL, "to": [recipient], "subject": "CRM EDIMCO - Test export email", "html": html}
    await asyncio.to_thread(resend.Emails.send, params)
    return {"message": f"Email test envoye a {recipient}"}

@router.get("/stats")
async def get_backup_stats(current_user: dict = Depends(get_current_user)):
    require_role(current_user, min_level=2)
    total = await db.backups.count_documents({})
    successful = await db.backups.count_documents({"status": "success"})
    failed = await db.backups.count_documents({"status": "failed"})
    last = await db.backups.find_one({"status": "success"}, sort=[("timestamp", -1)])
    total_size = 0
    async for b in db.backups.find({"status": "success", "size_mb": {"$exists": True}}):
        total_size += b.get("size_mb", 0)
    return {"total_backups": total, "successful": successful, "failed": failed, "total_size_mb": round(total_size, 2), "last_backup": last.get("timestamp") if last else None}


async def send_backup_alert_email(event_type: str, details: dict):
    try:
        if not resend.api_key:
            return
        notification_email = os.environ.get("NOTIFICATION_EMAIL", "")
        if not notification_email:
            return
        if event_type == "success":
            subject = "Sauvegarde reussie - CRM DJERBA"
            html = f"<div style='font-family:Arial;padding:20px;'><h2 style='color:#22c55e;'>Sauvegarde reussie</h2><p>Type: {details.get('backup_type','')}</p><p>Taille: {details.get('size_mb',0)} MB</p></div>"
        elif event_type == "failed":
            subject = "ECHEC Sauvegarde - CRM DJERBA"
            html = f"<div style='font-family:Arial;padding:20px;'><h2 style='color:#ef4444;'>Echec sauvegarde</h2><p>Erreur: {details.get('error','')}</p></div>"
        elif event_type == "restored":
            subject = "Restauration effectuee - CRM DJERBA"
            html = f"<div style='font-family:Arial;padding:20px;'><h2 style='color:#3b82f6;'>Base restauree</h2><p>Backup: {details.get('backup_id','')}</p></div>"
        else:
            return
        params = {"from": SENDER_EMAIL, "to": [notification_email], "subject": subject, "html": html}
        await asyncio.to_thread(resend.Emails.send, params)
    except Exception as e:
        logger.error(f"Backup alert email error: {e}")


# ============ SCHEDULER FUNCTIONS ============
async def scheduled_backup_6h():
    try:
        result = await backup_manager.create_backup(backup_type="auto_6h", triggered_by="Scheduler")
        result_db = {k: v for k, v in result.items() if k != "_id"}
        await db.backups.insert_one(result_db)
        if result["status"] == "failed":
            await send_backup_alert_email("failed", result)
        await backup_manager.apply_retention_policy()
    except Exception as e:
        logger.error(f"Scheduled 6h backup error: {e}")

async def scheduled_backup_daily():
    try:
        result = await backup_manager.create_backup(backup_type="auto_daily", triggered_by="Scheduler")
        result_db = {k: v for k, v in result.items() if k != "_id"}
        await db.backups.insert_one(result_db)
        if result["status"] == "failed":
            await send_backup_alert_email("failed", result)
        await backup_manager.apply_retention_policy()
    except Exception as e:
        logger.error(f"Scheduled daily backup error: {e}")

async def scheduled_weekly_email_export():
    try:
        settings = await db.notification_settings.find_one({"type": "backup_email_export"})
        if not settings or not settings.get("enabled", False):
            return
        recipient = settings.get("email") or os.environ.get("NOTIFICATION_EMAIL", "")
        if not recipient or not resend.api_key:
            return
        result = await backup_manager.create_backup(backup_type="weekly_export", triggered_by="Email Export")
        result_db = {k: v for k, v in result.items() if k != "_id"}
        await db.backups.insert_one(result_db)
        if result["status"] != "success":
            await send_backup_alert_email("failed", result)
            return
        backup_path = backup_manager.get_backup_path(result["backup_id"])
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for dirpath, dirnames, filenames in os.walk(backup_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    arcname = os.path.relpath(filepath, backup_path)
                    zf.write(filepath, arcname)
        zip_bytes = zip_buffer.getvalue()
        date_str = datetime.now(timezone.utc).strftime('%d/%m/%Y')
        size_kb = round(len(zip_bytes) / 1024, 1)
        client_count = await db.clients.count_documents({"deleted_at": None})
        appart_count = await db.appartements.count_documents({})
        html = f"<div style='font-family:Arial;max-width:600px;'><div style='background:#1E3A5F;color:white;padding:20px;text-align:center;'><h1 style='margin:0;font-size:20px;'>DJERBA CONSTRUCTION - CRM</h1></div><div style='padding:20px;background:#f8f9fa;'><h2 style='color:#1E3A5F;'>Sauvegarde hebdomadaire</h2><p>Copie du <strong>{date_str}</strong>.</p><p>Clients: {client_count} | Appartements: {appart_count} | Taille: {size_kb} KB</p></div></div>"
        zip_b64 = base64.b64encode(zip_bytes).decode()
        params = {"from": SENDER_EMAIL, "to": [recipient], "subject": f"CRM EDIMCO - Sauvegarde hebdomadaire {date_str}", "html": html, "attachments": [{"filename": f"backup_crm_{datetime.now(timezone.utc).strftime('%Y%m%d')}.zip", "content": zip_b64}]}
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Weekly backup email sent to {recipient}")
    except Exception as e:
        logger.error(f"Weekly email export error: {e}")
