import os
import asyncio
import logging
import httpx
import resend
from datetime import datetime, timezone, timedelta
from core.database import db

logger = logging.getLogger(__name__)

resend.api_key = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
ALERTS_SENDER_EMAIL = os.environ.get("ALERTS_SENDER_EMAIL", "alerts@djerbaconstruction.com")
ADMIN_ALERT_EMAIL = os.environ.get("ADMIN_ALERT_EMAIL", "saighryma@gmail.com")
LOGO_URL = "https://customer-assets.emergentagent.com/job_property-hub-612/artifacts/wry3uaf5_IMG_1081.jpeg"


async def get_ip_geolocation(ip: str) -> dict:
    try:
        if ip in ("127.0.0.1", "localhost", "::1", "testclient"):
            return {"city": "Local", "region": "", "country_name": "Serveur local"}
        async with httpx.AsyncClient(timeout=5) as client_http:
            resp = await client_http.get(f"https://ipapi.co/{ip}/json/")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "city": data.get("city", "Inconnu"),
                    "region": data.get("region", ""),
                    "country_name": data.get("country_name", "Inconnu")
                }
    except Exception as e:
        logger.warning(f"Geolocation lookup failed for {ip}: {e}")
    return {"city": "Inconnu", "region": "", "country_name": "Inconnu"}


def build_email_html(title: str, body_content: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
  <tr><td style="background:#172D66;padding:24px;text-align:center;">
    <img src="{LOGO_URL}" alt="Djerba Construction" height="60" style="height:60px;"/>
  </td></tr>
  <tr><td style="padding:32px 40px;">
    <h2 style="color:#172D66;margin:0 0 20px;font-size:20px;">{title}</h2>
    {body_content}
  </td></tr>
  <tr><td style="background:#f8f8f8;padding:16px 40px;text-align:center;border-top:1px solid #eee;">
    <p style="margin:0;font-size:12px;color:#888;">Djerba Construction &mdash; Notification automatique</p>
    <p style="margin:4px 0 0;font-size:11px;color:#aaa;">Ce message est envoy&eacute; automatiquement. Ne pas r&eacute;pondre.</p>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


async def send_security_alert(to_email: str, subject: str, title: str, body_content: str):
    try:
        if not resend.api_key:
            logger.warning("Resend API key not configured, skipping security alert")
            return
        html = build_email_html(title, body_content)
        sender = ALERTS_SENDER_EMAIL
        try:
            params = {"from": sender, "to": [to_email], "subject": subject, "html": html}
            await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"Security alert sent to {to_email}: {subject}")
        except Exception as send_err:
            if "not verified" in str(send_err).lower():
                params = {"from": SENDER_EMAIL, "to": [to_email], "subject": subject, "html": html}
                await asyncio.to_thread(resend.Emails.send, params)
                logger.info(f"Security alert sent (fallback sender) to {to_email}: {subject}")
            else:
                raise
    except Exception as e:
        logger.error(f"Failed to send security alert: {e}")


async def record_login_attempt(email: str, ip: str, user_agent: str, success: bool):
    await db.login_attempts.insert_one({
        "email": email.lower(),
        "ip": ip,
        "user_agent": user_agent,
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


async def get_failed_attempts_count(email: str) -> int:
    last_success = await db.login_attempts.find_one(
        {"email": email.lower(), "success": True},
        sort=[("timestamp", -1)]
    )
    query = {"email": email.lower(), "success": False}
    if last_success:
        query["timestamp"] = {"$gt": last_success["timestamp"]}
    return await db.login_attempts.count_documents(query)


async def is_new_ip_for_user(email: str, ip: str) -> bool:
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    existing = await db.login_attempts.find_one({
        "email": email.lower(),
        "ip": ip,
        "success": True,
        "timestamp": {"$gte": seven_days_ago}
    })
    return existing is None


async def alert_unknown_email(email: str, ip: str, user_agent: str, geo: dict):
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")
    location = f"{geo['city']}, {geo['country_name']}" if geo['city'] != 'Inconnu' else "Localisation inconnue"
    body = f"""
    <table width="100%" cellpadding="8" cellspacing="0" style="border:1px solid #fee2e2;border-radius:8px;background:#fef2f2;">
      <tr><td style="font-size:14px;color:#333;">
        <p style="margin:0 0 12px;"><strong style="color:#EF2A45;">Email tente :</strong> {email}</p>
        <p style="margin:0 0 12px;"><strong>Date/Heure :</strong> {now}</p>
        <p style="margin:0 0 12px;"><strong>Adresse IP :</strong> {ip}</p>
        <p style="margin:0 0 12px;"><strong>Localisation :</strong> {location}</p>
        <p style="margin:0;"><strong>Appareil :</strong> {user_agent[:100]}</p>
      </td></tr>
    </table>
    <p style="margin:16px 0 0;font-size:13px;color:#666;">Quelqu'un a tente de se connecter avec un email qui n'existe pas dans le systeme.</p>
    """
    await send_security_alert(
        ADMIN_ALERT_EMAIL,
        "\U0001f6a8 Tentative de connexion suspecte - Djerba Construction",
        "Tentative de connexion suspecte",
        body
    )


async def alert_account_locked(email: str, ip: str, user_agent: str, geo: dict, attempts: int):
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")
    location = f"{geo['city']}, {geo['country_name']}" if geo['city'] != 'Inconnu' else "Localisation inconnue"
    body = f"""
    <table width="100%" cellpadding="8" cellspacing="0" style="border:1px solid #fef3c7;border-radius:8px;background:#fffbeb;">
      <tr><td style="font-size:14px;color:#333;">
        <p style="margin:0 0 12px;"><strong style="color:#EF2A45;">Compte bloque :</strong> {email}</p>
        <p style="margin:0 0 12px;"><strong>Date/Heure :</strong> {now}</p>
        <p style="margin:0 0 12px;"><strong>Adresse IP :</strong> {ip}</p>
        <p style="margin:0 0 12px;"><strong>Localisation :</strong> {location}</p>
        <p style="margin:0 0 12px;"><strong>Tentatives echouees :</strong> {attempts}</p>
        <p style="margin:0;"><strong>Duree blocage :</strong> 15 minutes</p>
      </td></tr>
    </table>
    <p style="margin:16px 0 0;font-size:13px;color:#666;">Le compte a ete automatiquement bloque apres {attempts} tentatives echouees consecutives.</p>
    """
    await send_security_alert(
        ADMIN_ALERT_EMAIL,
        "\u26a0\ufe0f Compte bloque apres 5 echecs - Djerba Construction",
        "Compte bloque temporairement",
        body
    )


async def alert_new_ip_login(user_email: str, ip: str, user_agent: str, geo: dict):
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")
    location = f"{geo['city']}, {geo['country_name']}" if geo['city'] != 'Inconnu' else "Localisation inconnue"
    body = f"""
    <table width="100%" cellpadding="8" cellspacing="0" style="border:1px solid #d1fae5;border-radius:8px;background:#ecfdf5;">
      <tr><td style="font-size:14px;color:#333;">
        <p style="margin:0 0 12px;"><strong>Date/Heure :</strong> {now}</p>
        <p style="margin:0 0 12px;"><strong>Adresse IP :</strong> {ip}</p>
        <p style="margin:0 0 12px;"><strong>Localisation :</strong> {location}</p>
        <p style="margin:0;"><strong>Appareil :</strong> {user_agent[:100]}</p>
      </td></tr>
    </table>
    <p style="margin:16px 0 0;font-size:13px;color:#666;">Une connexion reussie a ete detectee depuis un nouvel appareil ou une nouvelle adresse IP.</p>
    <p style="margin:8px 0 0;font-size:13px;color:#EF2A45;font-weight:bold;">Si ce n'est pas vous, contactez immediatement l'administrateur.</p>
    """
    await send_security_alert(
        user_email,
        "\u2705 Nouvelle connexion a votre compte",
        "Nouvelle connexion detectee",
        body
    )


async def alert_ip_banned(ip: str, user_agent: str, geo: dict, attempts: int):
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")
    location = f"{geo['city']}, {geo['country_name']}" if geo['city'] != 'Inconnu' else "Localisation inconnue"
    body = f"""
    <table width="100%" cellpadding="8" cellspacing="0" style="border:1px solid #fecaca;border-radius:8px;background:#fef2f2;">
      <tr><td style="font-size:14px;color:#333;">
        <p style="margin:0 0 12px;"><strong style="color:#EF2A45;">IP BANNIE :</strong> {ip}</p>
        <p style="margin:0 0 12px;"><strong>Date/Heure :</strong> {now}</p>
        <p style="margin:0 0 12px;"><strong>Localisation :</strong> {location}</p>
        <p style="margin:0 0 12px;"><strong>Tentatives echouees :</strong> {attempts}</p>
        <p style="margin:0 0 12px;"><strong>Duree du ban :</strong> 1 heure</p>
        <p style="margin:0;"><strong>Appareil :</strong> {user_agent[:100]}</p>
      </td></tr>
    </table>
    <p style="margin:16px 0 0;font-size:13px;color:#666;">Cette adresse IP a ete automatiquement bloquee apres {attempts} tentatives de connexion echouees en moins d'une heure.</p>
    <p style="margin:8px 0 0;font-size:13px;color:#EF2A45;font-weight:bold;">Activite suspecte detectee. Possible tentative d'intrusion.</p>
    """
    await send_security_alert(
        ADMIN_ALERT_EMAIL,
        "\U0001f6ab IP bannie - Tentative d'intrusion - Djerba Construction",
        "Adresse IP bloquee automatiquement",
        body
    )
