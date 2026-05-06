"""WhatsApp webhook and AI routes"""
import os
import json
import hmac
import hashlib
import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends, Response
from starlette.responses import JSONResponse
from core.database import db, SOFT_DELETE_FILTER
from core.auth import get_current_user
from core.websocket import manager
from core.helpers import send_notification_email
from models.schemas import WhatsAppMessage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.get("/webhook")
async def verify_whatsapp_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == os.environ.get("WHATSAPP_VERIFY_TOKEN", ""):
        return Response(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def handle_whatsapp_webhook(request: Request):
    body = await request.body()
    app_secret = os.environ.get("META_APP_SECRET", "")
    if app_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if signature.startswith("sha256="):
            computed = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(computed, signature[7:]):
                raise HTTPException(status_code=403, detail="Invalid signature")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if payload.get("object") != "whatsapp_business_account":
        return JSONResponse(status_code=200, content={"status": "ok"})
    asyncio.create_task(process_whatsapp_webhook(payload))
    return JSONResponse(status_code=200, content={"status": "ok"})


async def process_whatsapp_webhook(payload: dict):
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if "messages" in value:
                    for message in value.get("messages", []):
                        await handle_incoming_message(message)
    except Exception as e:
        logger.error(f"WhatsApp webhook processing error: {e}")


async def handle_incoming_message(message: dict):
    sender = message.get("from")
    if message.get("type") != "text":
        return
    content = message.get("text", {}).get("body", "")
    logger.info(f"WhatsApp message from {sender}: {content}")
    ai_response = await generate_ai_response(sender, content)
    await db.whatsapp_conversations.insert_one({
        "message_id": message.get("id"), "phone": sender,
        "user_message": content, "ai_response": ai_response,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    await create_lead(sender, content, ai_response)
    await send_message(sender, ai_response)


async def generate_ai_response(phone: str, message: str) -> str:
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        residences = [r.get("nom", "") async for r in db.residences.find({})]
        appartements = []
        async for a in db.appartements.find({"statut": "disponible", **SOFT_DELETE_FILTER}):
            appartements.append({"type": a.get("type_appart", ""), "prix": a.get("prix", 0), "surface": a.get("surface_habitable", 0)})
        system_msg = f"""Tu es l'assistant virtuel de DJERBA CONSTRUCTION. Reponds en francais/arabe/anglais selon le client. Sois concis (2-3 phrases max). Residences: {', '.join(residences) if residences else 'Nos residences'}. Appartements disponibles: {len(appartements)}. Types: {', '.join(set(a['type'] for a in appartements)) if appartements else 'F2, F3, F4'}. Prix: {min(a['prix'] for a in appartements) if appartements else 0:,.0f} - {max(a['prix'] for a in appartements) if appartements else 0:,.0f} DA"""
        chat = LlmChat(api_key=os.environ.get("EMERGENT_LLM_KEY"), session_id=f"whatsapp_{phone}", system_message=system_msg).with_model("openai", "gpt-5.2")
        return await chat.send_message(UserMessage(text=message))
    except Exception as e:
        logger.error(f"WhatsApp AI error: {e}")
        return "Merci pour votre message. Un de nos conseillers vous contactera bientot."


async def send_message(recipient: str, message: str):
    import requests
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
    token = os.environ.get("META_ACCESS_TOKEN", "")
    if not phone_id or not token:
        return
    try:
        requests.post(f"https://graph.facebook.com/v18.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"messaging_product": "whatsapp", "to": recipient, "type": "text", "text": {"body": message}}, timeout=10)
    except Exception as e:
        logger.error(f"Failed to send WhatsApp: {e}")


async def create_lead(phone: str, message: str, ai_response: str):
    existing = await db.clients.find_one({"telephone": phone})
    if not existing:
        await db.clients.insert_one({
            "nom": f"Lead WhatsApp {phone[-4:]}", "telephone": phone, "email": None,
            "salaire": None, "situation_familiale": None, "notes": f"Premier message: {message}",
            "statut": "nouveau", "temperature": "tiede", "source": "whatsapp",
            "reference": None, "appartement_ids": [], "deleted_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(), "created_by": "whatsapp_bot"
        })
        await manager.broadcast({"type": "new_lead", "data": {"phone": phone}})
    else:
        await db.clients.update_one({"telephone": phone}, {"$set": {
            "notes": f"{existing.get('notes', '')}\n\n[{datetime.now().strftime('%d/%m/%Y %H:%M')}] {message}",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }})


@router.post("/message")
async def test_whatsapp_message(msg: WhatsAppMessage, current_user: dict = Depends(get_current_user)):
    ai_response = await generate_ai_response(msg.phone, msg.message)
    await db.whatsapp_conversations.insert_one({"phone": msg.phone, "user_message": msg.message, "ai_response": ai_response, "test": True, "created_at": datetime.now(timezone.utc).isoformat()})
    return {"response": ai_response, "phone": msg.phone}

@router.get("/conversations")
async def get_conversations(current_user: dict = Depends(get_current_user)):
    result = []
    async for c in db.whatsapp_conversations.find({}).sort("created_at", -1).limit(50):
        result.append({"id": str(c["_id"]), "phone": c.get("phone", ""), "user_message": c.get("user_message", ""), "ai_response": c.get("ai_response", ""), "created_at": c.get("created_at", "")})
    return result
