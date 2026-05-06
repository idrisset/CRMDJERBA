import os
import asyncio
import logging
import resend
from datetime import datetime, timezone
from core.database import db

logger = logging.getLogger(__name__)

resend.api_key = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")


async def audit_log(user: dict, action: str, entity_type: str, entity_id: str, entity_name: str = "", old_values: dict = None, new_values: dict = None):
    doc = {
        "user_id": user.get("_id", "system"),
        "user_name": user.get("name", user.get("email", "system")),
        "user_email": user.get("email", ""),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "old_values": old_values,
        "new_values": new_values,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(doc)


async def generate_client_reference() -> str:
    last = await db.clients.find_one(
        {"reference": {"$exists": True, "$ne": None}},
        sort=[("reference", -1)]
    )
    if last and last.get("reference"):
        try:
            num = int(last["reference"].replace("#", "")) + 1
        except ValueError:
            num = 1
    else:
        num = 1
    return f"#{num:03d}"


async def check_duplicate_client(nom: str, telephone: str, email: str = None, exclude_id: str = None):
    from bson import ObjectId
    from core.database import SOFT_DELETE_FILTER
    conditions = []
    if telephone:
        conditions.append({"telephone": telephone})
        conditions.append({"telephone2": telephone})
    if email:
        conditions.append({"email": {"$regex": f"^{email}$", "$options": "i"}})
    if nom:
        conditions.append({"nom": {"$regex": f"^{nom}$", "$options": "i"}})
    if not conditions:
        return []
    query = {"$or": conditions, **SOFT_DELETE_FILTER}
    if exclude_id:
        query["_id"] = {"$ne": ObjectId(exclude_id)}
    duplicates = []
    async for c in db.clients.find(query):
        reasons = []
        if telephone and (c.get("telephone") == telephone or c.get("telephone2") == telephone):
            reasons.append("telephone")
        if email and c.get("email", "").lower() == email.lower():
            reasons.append("email")
        if nom and c.get("nom", "").lower() == nom.lower():
            reasons.append("nom")
        if reasons:
            duplicates.append({
                "id": str(c["_id"]),
                "reference": c.get("reference", ""),
                "nom": c.get("nom", ""),
                "telephone": c.get("telephone", ""),
                "email": c.get("email", ""),
                "reasons": reasons
            })
    return duplicates


async def send_notification_email(subject: str, html_content: str):
    try:
        settings = await db.settings.find_one({"type": "notifications"})
        if not settings or not settings.get("email_enabled"):
            return
        recipients = settings.get("notification_emails", [])
        if not recipients:
            return
        for email in recipients:
            params = {"from": SENDER_EMAIL, "to": [email], "subject": subject, "html": html_content}
            await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"Notification email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")
