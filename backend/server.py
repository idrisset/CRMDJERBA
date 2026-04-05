from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import bcrypt
import jwt
import hmac
import hashlib
import asyncio
import resend
import json
import io
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Resend config
resend.api_key = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

# JWT Config
JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

# Password utils
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# JWT utils
def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "type": "access"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

# Auth dependency
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Type de token invalide")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

# Models
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "commercial"

class ClientCreate(BaseModel):
    nom: str
    telephone: str
    telephone2: Optional[str] = None
    email: Optional[str] = None
    salaire: Optional[float] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    objectif: Optional[str] = None
    mode_paiement: Optional[str] = None
    etage_souhaite: Optional[str] = None
    situation_familiale: Optional[str] = None
    notes: Optional[str] = None
    statut: str = "nouveau"
    appartement_id: Optional[str] = None

class ClientUpdate(BaseModel):
    nom: Optional[str] = None
    telephone: Optional[str] = None
    telephone2: Optional[str] = None
    email: Optional[str] = None
    salaire: Optional[float] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    objectif: Optional[str] = None
    mode_paiement: Optional[str] = None
    etage_souhaite: Optional[str] = None
    situation_familiale: Optional[str] = None
    notes: Optional[str] = None
    statut: Optional[str] = None
    appartement_id: Optional[str] = None

class ResidenceCreate(BaseModel):
    nom: str
    adresse: Optional[str] = None
    description: Optional[str] = None

class ResidenceUpdate(BaseModel):
    nom: Optional[str] = None
    adresse: Optional[str] = None
    description: Optional[str] = None

# ===== PROSPECTS (Fiche client immobilière - Big Data) =====
class ProspectCreate(BaseModel):
    nom: str
    telephone: str
    telephone2: Optional[str] = None
    email: Optional[str] = None
    ville: Optional[str] = None
    quartier: Optional[str] = None
    type_logement: Optional[str] = None
    etage_souhaite: Optional[str] = None
    nombre_pieces: Optional[int] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    mode_paiement: Optional[str] = None
    objectif: Optional[str] = None
    situation_familiale: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = "foire"

class ProspectUpdate(BaseModel):
    nom: Optional[str] = None
    telephone: Optional[str] = None
    telephone2: Optional[str] = None
    email: Optional[str] = None
    ville: Optional[str] = None
    quartier: Optional[str] = None
    type_logement: Optional[str] = None
    etage_souhaite: Optional[str] = None
    nombre_pieces: Optional[int] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    mode_paiement: Optional[str] = None
    objectif: Optional[str] = None
    situation_familiale: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None

class AppartementCreate(BaseModel):
    residence_id: str
    type_appart: str
    prix: float
    etage: str = ""
    statut: str = "disponible"
    surface: Optional[float] = None
    surface_habitable: Optional[float] = None
    surface_utile: Optional[float] = None
    description: Optional[str] = None
    bloc: Optional[str] = None
    numero_lot: Optional[str] = None
    destination: Optional[str] = None

class AppartementUpdate(BaseModel):
    type_appart: Optional[str] = None
    prix: Optional[float] = None
    etage: Optional[str] = None
    statut: Optional[str] = None
    surface: Optional[float] = None
    surface_habitable: Optional[float] = None
    surface_utile: Optional[float] = None
    description: Optional[str] = None
    client_id: Optional[str] = None
    bloc: Optional[str] = None
    numero_lot: Optional[str] = None
    destination: Optional[str] = None

class WhatsAppMessage(BaseModel):
    phone: str
    message: str

class NotificationSettings(BaseModel):
    email_enabled: bool = True
    notification_emails: List[str] = []

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Create the app
app = FastAPI(title="DJERBA CONSTRUCTION CRM API")
api_router = APIRouter(prefix="/api")

# CORS - Allow all origins for mobile compatibility
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============ HELPER FUNCTIONS ============
async def send_notification_email(subject: str, html_content: str):
    """Send notification email to all configured recipients"""
    try:
        settings = await db.settings.find_one({"type": "notifications"})
        if not settings or not settings.get("email_enabled"):
            return
        
        recipients = settings.get("notification_emails", [])
        if not recipients:
            return
        
        for email in recipients:
            params = {
                "from": SENDER_EMAIL,
                "to": [email],
                "subject": subject,
                "html": html_content
            }
            await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"Notification email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")

async def create_lead_from_whatsapp(phone: str, message: str, ai_response: str):
    """Create or update lead from WhatsApp conversation"""
    existing = await db.clients.find_one({"telephone": phone})
    
    if not existing:
        # Create new lead
        lead_doc = {
            "nom": f"Lead WhatsApp {phone[-4:]}",
            "telephone": phone,
            "email": None,
            "salaire": None,
            "situation_familiale": None,
            "notes": f"Premier message: {message}",
            "statut": "nouveau",
            "temperature": "tiède",
            "source": "whatsapp",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "whatsapp_bot"
        }
        result = await db.clients.insert_one(lead_doc)
        
        # Send notification
        await send_notification_email(
            subject="🔔 Nouveau lead WhatsApp - DJERBA CONSTRUCTION",
            html_content=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #1E3A5F; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">DJERBA CONSTRUCTION</h1>
                </div>
                <div style="padding: 20px; background: #f8f9fa;">
                    <h2 style="color: #1E3A5F;">Nouveau lead reçu via WhatsApp</h2>
                    <p><strong>Téléphone:</strong> {phone}</p>
                    <p><strong>Message:</strong> {message}</p>
                    <p><strong>Réponse IA:</strong> {ai_response[:200]}...</p>
                    <a href="{os.environ.get('FRONTEND_URL')}/clients" 
                       style="display: inline-block; background: #C41E3A; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin-top: 16px;">
                        Voir dans le CRM
                    </a>
                </div>
            </div>
            """
        )
        
        await manager.broadcast({"type": "new_lead", "data": {"phone": phone}})
        return str(result.inserted_id)
    else:
        # Update existing client notes
        await db.clients.update_one(
            {"telephone": phone},
            {"$set": {
                "notes": f"{existing.get('notes', '')}\n\n[{datetime.now().strftime('%d/%m/%Y %H:%M')}] {message}",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return str(existing["_id"])

# ============ AUTH ROUTES ============
@api_router.post("/auth/register")
async def register(user: UserRegister):
    existing = await db.users.find_one({"email": user.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    user_doc = {
        "email": user.email.lower(),
        "password_hash": hash_password(user.password),
        "name": user.name,
        "role": user.role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, user.email)
    refresh_token = create_refresh_token(user_id)
    
    return {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "access_token": access_token,
        "refresh_token": refresh_token
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email.lower()})
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, user["email"])
    refresh_token = create_refresh_token(user_id)
    
    return {
        "id": user_id,
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user.get("role", "commercial"),
        "access_token": access_token,
        "refresh_token": refresh_token
    }

@api_router.post("/auth/logout")
async def logout():
    response = JSONResponse(content={"message": "Déconnexion réussie"})
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return response

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@api_router.post("/auth/refresh")
async def refresh_token(request: Request):
    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=401, detail="Token de rafraîchissement manquant")
    try:
        payload = jwt.decode(refresh, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Type de token invalide")
        
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        access_token = create_access_token(str(user["_id"]), user["email"])
        response = JSONResponse(content={"message": "Token rafraîchi"})
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=3600, path="/")
        return response
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

# ============ CLIENTS ROUTES ============
@api_router.get("/clients")
async def get_clients(current_user: dict = Depends(get_current_user)):
    result = []
    async for c in db.clients.find({}):
        client_data = {
            "id": str(c["_id"]),
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
            "appartement_id": c.get("appartement_id"),
            "source": c.get("source", "manual"),
            "created_at": c.get("created_at", ""),
            "created_by": c.get("created_by", "")
        }
        result.append(client_data)
    return result

@api_router.post("/clients")
async def create_client(client: ClientCreate, current_user: dict = Depends(get_current_user)):
    client_data = client.model_dump()
    appartement_id = client_data.pop("appartement_id", None)
    
    client_doc = {
        **client_data,
        "appartement_id": appartement_id,
        "source": "manual",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["_id"]
    }
    result = await db.clients.insert_one(client_doc)
    client_id = str(result.inserted_id)
    
    # If apartment assigned, block it
    if appartement_id:
        appart = await db.appartements.find_one({"_id": ObjectId(appartement_id)})
        if appart and appart.get("statut") == "disponible":
            await db.appartements.update_one(
                {"_id": ObjectId(appartement_id)},
                {"$set": {"statut": "réservé", "client_id": client_id}}
            )
            # Log reservation history
            await db.reservations.insert_one({
                "client_id": client_id,
                "client_nom": client_data.get("nom", ""),
                "appartement_id": appartement_id,
                "bloc": appart.get("bloc", ""),
                "numero_lot": appart.get("numero_lot", ""),
                "type_appart": appart.get("type_appart", ""),
                "action": "réservé",
                "agent": current_user.get("name", current_user.get("email", "")),
                "date": datetime.now(timezone.utc).isoformat()
            })
            await manager.broadcast({"type": "appartement_updated", "data": {"id": appartement_id}})
    
    await manager.broadcast({"type": "client_created", "data": {"id": client_id}})
    return {"id": client_id, **client_data}

@api_router.put("/clients/{client_id}")
async def update_client(client_id: str, client: ClientUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in client.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user["_id"]
    
    # Get existing client to check old apartment
    existing = await db.clients.find_one({"_id": ObjectId(client_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    old_appart_id = existing.get("appartement_id")
    new_appart_id = client.appartement_id
    
    # If apartment changed, handle reservation logic
    if new_appart_id is not None and new_appart_id != old_appart_id:
        # Release old apartment
        if old_appart_id:
            await db.appartements.update_one(
                {"_id": ObjectId(old_appart_id)},
                {"$set": {"statut": "disponible", "client_id": None}}
            )
            await db.reservations.insert_one({
                "client_id": client_id,
                "client_nom": existing.get("nom", ""),
                "appartement_id": old_appart_id,
                "action": "libéré",
                "agent": current_user.get("name", current_user.get("email", "")),
                "date": datetime.now(timezone.utc).isoformat()
            })
            await manager.broadcast({"type": "appartement_updated", "data": {"id": old_appart_id}})
        
        # Block new apartment
        if new_appart_id and new_appart_id != "none":
            appart = await db.appartements.find_one({"_id": ObjectId(new_appart_id)})
            if appart:
                # Check if already taken by someone else
                if appart.get("statut") != "disponible" and appart.get("client_id") and appart.get("client_id") != client_id:
                    raise HTTPException(status_code=409, detail=f"Lot {appart.get('numero_lot')} déjà réservé par un autre client")
                
                await db.appartements.update_one(
                    {"_id": ObjectId(new_appart_id)},
                    {"$set": {"statut": "réservé", "client_id": client_id}}
                )
                await db.reservations.insert_one({
                    "client_id": client_id,
                    "client_nom": update_data.get("nom", existing.get("nom", "")),
                    "appartement_id": new_appart_id,
                    "bloc": appart.get("bloc", ""),
                    "numero_lot": appart.get("numero_lot", ""),
                    "type_appart": appart.get("type_appart", ""),
                    "action": "réservé",
                    "agent": current_user.get("name", current_user.get("email", "")),
                    "date": datetime.now(timezone.utc).isoformat()
                })
                # Auto-set client status to réservé
                update_data["statut"] = "réservé"
                await manager.broadcast({"type": "appartement_updated", "data": {"id": new_appart_id}})
        else:
            # Removing apartment assignment
            update_data["appartement_id"] = None
    elif client.statut == "vendu" and old_appart_id:
        # Mark apartment as sold
        await db.appartements.update_one(
            {"_id": ObjectId(old_appart_id)},
            {"$set": {"statut": "vendu"}}
        )
        await db.reservations.insert_one({
            "client_id": client_id,
            "client_nom": update_data.get("nom", existing.get("nom", "")),
            "appartement_id": old_appart_id,
            "action": "vendu",
            "agent": current_user.get("name", current_user.get("email", "")),
            "date": datetime.now(timezone.utc).isoformat()
        })
        await manager.broadcast({"type": "appartement_updated", "data": {"id": old_appart_id}})
    
    result = await db.clients.update_one(
        {"_id": ObjectId(client_id)},
        {"$set": update_data}
    )
    
    await manager.broadcast({"type": "client_updated", "data": {"id": client_id}})
    return {"id": client_id, **update_data}

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
    # Release any apartment assigned to this client
    existing = await db.clients.find_one({"_id": ObjectId(client_id)})
    if existing and existing.get("appartement_id"):
        await db.appartements.update_one(
            {"_id": ObjectId(existing["appartement_id"])},
            {"$set": {"statut": "disponible", "client_id": None}}
        )
        await manager.broadcast({"type": "appartement_updated", "data": {"id": existing["appartement_id"]}})
    
    result = await db.clients.delete_one({"_id": ObjectId(client_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    await manager.broadcast({"type": "client_deleted", "data": {"id": client_id}})
    return {"message": "Client supprimé"}

# ============ RESIDENCES ROUTES ============
@api_router.get("/residences")
async def get_residences(current_user: dict = Depends(get_current_user)):
    result = []
    async for r in db.residences.find({}):
        result.append({
            "id": str(r["_id"]),
            "nom": r.get("nom", ""),
            "adresse": r.get("adresse", ""),
            "description": r.get("description", "")
        })
    return result

@api_router.post("/residences")
async def create_residence(residence: ResidenceCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Seul l'admin peut créer des résidences")
    
    residence_doc = {
        **residence.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.residences.insert_one(residence_doc)
    
    await manager.broadcast({"type": "residence_created", "data": {"id": str(result.inserted_id)}})
    
    return {"id": str(result.inserted_id), **residence.model_dump()}

@api_router.put("/residences/{residence_id}")
async def update_residence(residence_id: str, residence: ResidenceUpdate, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Seul l'admin peut modifier les résidences")
    
    update_data = {k: v for k, v in residence.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
    
    result = await db.residences.update_one(
        {"_id": ObjectId(residence_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Résidence non trouvée")
    
    await manager.broadcast({"type": "residence_updated", "data": {"id": residence_id}})
    
    return {"id": residence_id, **update_data}

@api_router.delete("/residences/{residence_id}")
async def delete_residence(residence_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Seul l'admin peut supprimer des résidences")
    
    result = await db.residences.delete_one({"_id": ObjectId(residence_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Résidence non trouvée")
    
    await manager.broadcast({"type": "residence_deleted", "data": {"id": residence_id}})
    
    return {"message": "Résidence supprimée"}

# ============ PROSPECTS ROUTES (Fiche client immobilière) ============
@api_router.get("/prospects")
async def get_prospects(current_user: dict = Depends(get_current_user)):
    result = []
    async for p in db.prospects.find({}).sort("created_at", -1):
        result.append({
            "id": str(p["_id"]),
            "nom": p.get("nom", ""),
            "telephone": p.get("telephone", ""),
            "telephone2": p.get("telephone2", ""),
            "email": p.get("email", ""),
            "ville": p.get("ville", ""),
            "quartier": p.get("quartier", ""),
            "type_logement": p.get("type_logement", ""),
            "etage_souhaite": p.get("etage_souhaite", ""),
            "nombre_pieces": p.get("nombre_pieces"),
            "budget_min": p.get("budget_min"),
            "budget_max": p.get("budget_max"),
            "mode_paiement": p.get("mode_paiement", ""),
            "objectif": p.get("objectif", ""),
            "situation_familiale": p.get("situation_familiale", ""),
            "notes": p.get("notes", ""),
            "source": p.get("source", "foire"),
            "created_at": p.get("created_at", ""),
        })
    return result

@api_router.post("/prospects")
async def create_prospect(prospect: ProspectCreate, current_user: dict = Depends(get_current_user)):
    doc = {
        **prospect.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["_id"]
    }
    result = await db.prospects.insert_one(doc)
    await manager.broadcast({"type": "prospect_created", "data": {"id": str(result.inserted_id)}})
    return {"id": str(result.inserted_id), **prospect.model_dump()}

@api_router.put("/prospects/{prospect_id}")
async def update_prospect(prospect_id: str, prospect: ProspectUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in prospect.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnée")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.prospects.update_one({"_id": ObjectId(prospect_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Prospect non trouvé")
    await manager.broadcast({"type": "prospect_updated", "data": {"id": prospect_id}})
    return {"id": prospect_id, **update_data}

@api_router.delete("/prospects/{prospect_id}")
async def delete_prospect(prospect_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.prospects.delete_one({"_id": ObjectId(prospect_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prospect non trouvé")
    await manager.broadcast({"type": "prospect_deleted", "data": {"id": prospect_id}})
    return {"message": "Prospect supprimé"}

@api_router.get("/prospects/analytics")
async def get_prospects_analytics(current_user: dict = Depends(get_current_user)):
    total = await db.prospects.count_documents({})
    
    # Top villes
    villes_pipeline = [
        {"$match": {"ville": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$ville", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    villes = []
    async for v in db.prospects.aggregate(villes_pipeline):
        villes.append({"name": v["_id"], "count": v["count"]})
    
    # Top quartiers
    quartiers_pipeline = [
        {"$match": {"quartier": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$quartier", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    quartiers = []
    async for q in db.prospects.aggregate(quartiers_pipeline):
        quartiers.append({"name": q["_id"], "count": q["count"]})
    
    # Types de logement
    types_pipeline = [
        {"$match": {"type_logement": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$type_logement", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    types = []
    async for t in db.prospects.aggregate(types_pipeline):
        types.append({"name": t["_id"], "count": t["count"]})
    
    # Objectifs
    objectifs_pipeline = [
        {"$match": {"objectif": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$objectif", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    objectifs = []
    async for o in db.prospects.aggregate(objectifs_pipeline):
        objectifs.append({"name": o["_id"], "count": o["count"]})
    
    # Budget moyen
    budget_pipeline = [
        {"$match": {"budget_max": {"$ne": None, "$gt": 0}}},
        {"$group": {"_id": None, "avg_min": {"$avg": "$budget_min"}, "avg_max": {"$avg": "$budget_max"}}}
    ]
    budget_avg = {"avg_min": 0, "avg_max": 0}
    async for b in db.prospects.aggregate(budget_pipeline):
        budget_avg = {"avg_min": b.get("avg_min", 0) or 0, "avg_max": b.get("avg_max", 0) or 0}
    
    # Mode de paiement
    paiement_pipeline = [
        {"$match": {"mode_paiement": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$mode_paiement", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    paiements = []
    async for p in db.prospects.aggregate(paiement_pipeline):
        paiements.append({"name": p["_id"], "count": p["count"]})

    # Top villes + quartiers combined
    ville_quartier_pipeline = [
        {"$match": {"ville": {"$ne": None, "$ne": ""}, "quartier": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": {"ville": "$ville", "quartier": "$quartier"}, "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 15}
    ]
    zones = []
    async for z in db.prospects.aggregate(ville_quartier_pipeline):
        zones.append({"ville": z["_id"]["ville"], "quartier": z["_id"]["quartier"], "count": z["count"]})

    return {
        "total": total,
        "top_villes": villes,
        "top_quartiers": quartiers,
        "top_types": types,
        "objectifs": objectifs,
        "budget_avg": budget_avg,
        "modes_paiement": paiements,
        "top_zones": zones
    }

# ============ DASHBOARD ROUTES ============

# ============ APPARTEMENTS ROUTES ============
@api_router.get("/appartements")
async def get_appartements(current_user: dict = Depends(get_current_user)):
    result = []
    async for a in db.appartements.find({}):
        result.append({
            "id": str(a["_id"]),
            "residence_id": a.get("residence_id", ""),
            "type_appart": a.get("type_appart", ""),
            "prix": a.get("prix", 0),
            "etage": a.get("etage", ""),
            "statut": a.get("statut", "disponible"),
            "surface": a.get("surface"),
            "surface_habitable": a.get("surface_habitable"),
            "surface_utile": a.get("surface_utile"),
            "description": a.get("description", ""),
            "client_id": a.get("client_id"),
            "bloc": a.get("bloc", ""),
            "numero_lot": a.get("numero_lot", ""),
            "destination": a.get("destination", "")
        })
    return result

@api_router.post("/appartements")
async def create_appartement(appart: AppartementCreate, current_user: dict = Depends(get_current_user)):
    appart_doc = {
        **appart.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["_id"]
    }
    result = await db.appartements.insert_one(appart_doc)
    
    await manager.broadcast({"type": "appartement_created", "data": {"id": str(result.inserted_id)}})
    
    return {"id": str(result.inserted_id), **appart.model_dump()}

@api_router.put("/appartements/{appart_id}")
async def update_appartement(appart_id: str, appart: AppartementUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in appart.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
    
    existing = await db.appartements.find_one({"_id": ObjectId(appart_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Appartement non trouvé")
    
    old_client_id = existing.get("client_id")
    new_client_id = appart.client_id
    
    # Assigning a client to apartment
    if new_client_id and new_client_id != "none" and new_client_id != old_client_id:
        await db.clients.update_one(
            {"_id": ObjectId(new_client_id)},
            {"$set": {"appartement_id": appart_id, "statut": "réservé"}}
        )
        update_data["statut"] = update_data.get("statut", "réservé")
        await db.reservations.insert_one({
            "client_id": new_client_id,
            "appartement_id": appart_id,
            "bloc": existing.get("bloc", ""),
            "numero_lot": existing.get("numero_lot", ""),
            "type_appart": existing.get("type_appart", ""),
            "action": update_data.get("statut", "réservé"),
            "agent": current_user.get("name", current_user.get("email", "")),
            "date": datetime.now(timezone.utc).isoformat()
        })
        # Release old client if different
        if old_client_id and old_client_id != new_client_id:
            await db.clients.update_one(
                {"_id": ObjectId(old_client_id)},
                {"$set": {"appartement_id": None}}
            )
        await manager.broadcast({"type": "client_updated", "data": {"id": new_client_id}})
    elif appart.statut == "disponible" and old_client_id:
        # Releasing apartment
        await db.clients.update_one(
            {"_id": ObjectId(old_client_id)},
            {"$set": {"appartement_id": None}}
        )
        update_data["client_id"] = None
        await db.reservations.insert_one({
            "client_id": old_client_id,
            "appartement_id": appart_id,
            "bloc": existing.get("bloc", ""),
            "numero_lot": existing.get("numero_lot", ""),
            "action": "libéré",
            "agent": current_user.get("name", current_user.get("email", "")),
            "date": datetime.now(timezone.utc).isoformat()
        })
        await manager.broadcast({"type": "client_updated", "data": {"id": old_client_id}})
    
    result = await db.appartements.update_one(
        {"_id": ObjectId(appart_id)},
        {"$set": update_data}
    )
    
    await manager.broadcast({"type": "appartement_updated", "data": {"id": appart_id}})
    return {"id": appart_id, **update_data}

@api_router.delete("/appartements/{appart_id}")
async def delete_appartement(appart_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.appartements.delete_one({"_id": ObjectId(appart_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appartement non trouvé")
    
    await manager.broadcast({"type": "appartement_deleted", "data": {"id": appart_id}})
    
    return {"message": "Appartement supprimé"}

# ============ RESERVATIONS HISTORY ============
@api_router.get("/reservations")
async def get_reservations(current_user: dict = Depends(get_current_user)):
    result = []
    async for r in db.reservations.find({}).sort("date", -1).limit(100):
        result.append({
            "id": str(r["_id"]),
            "client_id": r.get("client_id", ""),
            "client_nom": r.get("client_nom", ""),
            "appartement_id": r.get("appartement_id", ""),
            "bloc": r.get("bloc", ""),
            "numero_lot": r.get("numero_lot", ""),
            "type_appart": r.get("type_appart", ""),
            "action": r.get("action", ""),
            "agent": r.get("agent", ""),
            "date": r.get("date", "")
        })
    return result
@api_router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    total_clients = await db.clients.count_documents({})
    total_appartements = await db.appartements.count_documents({})
    apparts_disponibles = await db.appartements.count_documents({"statut": "disponible"})
    apparts_reserves = await db.appartements.count_documents({"statut": "réservé"})
    apparts_vendus = await db.appartements.count_documents({"statut": "vendu"})
    
    clients_nouveau = await db.clients.count_documents({"statut": "nouveau"})
    clients_interesse = await db.clients.count_documents({"statut": "intéressé"})
    clients_visite = await db.clients.count_documents({"statut": "visite"})
    clients_reserve = await db.clients.count_documents({"statut": "réservé"})
    clients_vendu = await db.clients.count_documents({"statut": "vendu"})
    
    # Temperature breakdown
    clients_chaud = await db.clients.count_documents({"temperature": "chaud"})
    clients_tiede = await db.clients.count_documents({"temperature": "tiède"})
    clients_froid = await db.clients.count_documents({"temperature": "froid"})
    
    # WhatsApp leads
    whatsapp_leads = await db.clients.count_documents({"source": "whatsapp"})
    
    recent_clients = []
    async for c in db.clients.find({}).sort("created_at", -1).limit(5):
        recent_clients.append({
            "id": str(c["_id"]),
            "nom": c.get("nom", ""),
            "statut": c.get("statut", ""),
            "temperature": c.get("temperature", "froid"),
            "source": c.get("source", "manual"),
            "created_at": c.get("created_at", "")
        })
    
    # Logements only stats
    total_logements = await db.appartements.count_documents({"destination": "Logement"})
    logements_disponibles = await db.appartements.count_documents({"destination": "Logement", "statut": "disponible"})
    logements_reserves = await db.appartements.count_documents({"destination": "Logement", "statut": "réservé"})
    logements_vendus = await db.appartements.count_documents({"destination": "Logement", "statut": "vendu"})
    
    # Stats by bloc
    blocs_stats = {}
    for bloc in ["A", "B", "C", "D", "E", "F", "G", "H"]:
        blocs_stats[bloc] = {
            "total": await db.appartements.count_documents({"bloc": bloc, "destination": "Logement"}),
            "disponible": await db.appartements.count_documents({"bloc": bloc, "destination": "Logement", "statut": "disponible"}),
            "reserve": await db.appartements.count_documents({"bloc": bloc, "destination": "Logement", "statut": "réservé"}),
            "vendu": await db.appartements.count_documents({"bloc": bloc, "destination": "Logement", "statut": "vendu"}),
        }
    
    return {
        "total_clients": total_clients,
        "total_appartements": total_appartements,
        "total_logements": total_logements,
        "logements_disponibles": logements_disponibles,
        "logements_reserves": logements_reserves,
        "logements_vendus": logements_vendus,
        "appartements_disponibles": apparts_disponibles,
        "appartements_reserves": apparts_reserves,
        "appartements_vendus": apparts_vendus,
        "clients_par_statut": {
            "nouveau": clients_nouveau,
            "intéressé": clients_interesse,
            "visite": clients_visite,
            "réservé": clients_reserve,
            "vendu": clients_vendu
        },
        "clients_par_temperature": {
            "chaud": clients_chaud,
            "tiède": clients_tiede,
            "froid": clients_froid
        },
        "whatsapp_leads": whatsapp_leads,
        "recent_clients": recent_clients,
        "blocs_stats": blocs_stats
    }

# ============ WHATSAPP WEBHOOK (Meta Business API) ============
@api_router.get("/whatsapp/webhook")
async def verify_whatsapp_webhook(request: Request):
    """Verify webhook for Meta WhatsApp Business API"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
    
    if mode == "subscribe" and token == verify_token:
        logger.info("WhatsApp webhook verified")
        return Response(content=challenge, status_code=200)
    
    logger.warning("WhatsApp webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")

@api_router.post("/whatsapp/webhook")
async def handle_whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages from Meta Business API"""
    body = await request.body()
    
    # Verify signature (if APP_SECRET is configured)
    app_secret = os.environ.get("META_APP_SECRET", "")
    if app_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if signature.startswith("sha256="):
            expected_signature = signature[7:]
            computed_hash = hmac.new(
                app_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(computed_hash, expected_signature):
                logger.error("Invalid WhatsApp webhook signature")
                raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    if payload.get("object") != "whatsapp_business_account":
        return JSONResponse(status_code=200, content={"status": "ok"})
    
    # Process messages asynchronously
    asyncio.create_task(process_whatsapp_webhook(payload))
    
    return JSONResponse(status_code=200, content={"status": "ok"})

async def process_whatsapp_webhook(payload: dict):
    """Process incoming WhatsApp messages"""
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                if "messages" in value:
                    for message in value.get("messages", []):
                        await handle_incoming_whatsapp_message(message)
    except Exception as e:
        logger.error(f"WhatsApp webhook processing error: {e}")

async def handle_incoming_whatsapp_message(message: dict):
    """Handle a single incoming WhatsApp message"""
    message_id = message.get("id")
    sender = message.get("from")
    message_type = message.get("type", "text")
    
    if message_type != "text":
        return
    
    message_content = message.get("text", {}).get("body", "")
    
    logger.info(f"WhatsApp message from {sender}: {message_content}")
    
    # Generate AI response
    ai_response = await generate_whatsapp_ai_response(sender, message_content)
    
    # Store conversation
    await db.whatsapp_conversations.insert_one({
        "message_id": message_id,
        "phone": sender,
        "user_message": message_content,
        "ai_response": ai_response,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Create or update lead
    await create_lead_from_whatsapp(sender, message_content, ai_response)
    
    # Send response via WhatsApp API (if configured)
    await send_whatsapp_message(sender, ai_response)

async def generate_whatsapp_ai_response(phone: str, message: str) -> str:
    """Generate AI response for WhatsApp message"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Get residences and apartments for context
        residences = []
        async for r in db.residences.find({}):
            residences.append(r.get("nom", ""))
        
        appartements = []
        async for a in db.appartements.find({"statut": "disponible"}):
            appartements.append({
                "type": a.get("type_appart", ""),
                "prix": a.get("prix", 0),
                "etage": a.get("etage", 0),
                "surface": a.get("surface", 0)
            })
        
        system_message = f"""Tu es l'assistant virtuel de DJERBA CONSTRUCTION, une entreprise immobilière de qualité.
Tu réponds en français, en arabe ou en anglais selon la langue du client.
Tu dois:
1. Répondre aux questions sur les appartements disponibles
2. Poser des questions pour qualifier le prospect (budget, type recherché, localisation)
3. Collecter les informations de contact (nom, email si possible)
4. Être professionnel et accueillant

Résidences disponibles: {', '.join(residences) if residences else 'Nos résidences premium'}
Appartements disponibles: {len(appartements)}
Types: {', '.join(set(a['type'] for a in appartements)) if appartements else 'F2, F3, F4'}
Prix: {min(a['prix'] for a in appartements) if appartements else 0:,.0f} DA - {max(a['prix'] for a in appartements) if appartements else 0:,.0f} DA

Sois concis et professionnel. Maximum 2-3 phrases par réponse.
"""
        
        chat = LlmChat(
            api_key=os.environ.get("EMERGENT_LLM_KEY"),
            session_id=f"whatsapp_{phone}",
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=message)
        response = await chat.send_message(user_message)
        
        return response
    except Exception as e:
        logger.error(f"WhatsApp AI error: {e}")
        return "Merci pour votre message. Un de nos conseillers vous contactera bientôt. للتواصل: +213770481500"

async def send_whatsapp_message(recipient: str, message: str):
    """Send WhatsApp message via Meta Business API"""
    import requests
    
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
    access_token = os.environ.get("META_ACCESS_TOKEN", "")
    
    if not phone_number_id or not access_token:
        logger.warning("WhatsApp API not configured - message not sent")
        return
    
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"WhatsApp message sent to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")

# ============ WHATSAPP TEST ROUTES ============
@api_router.post("/whatsapp/message")
async def test_whatsapp_message(msg: WhatsAppMessage, current_user: dict = Depends(get_current_user)):
    """Test WhatsApp AI response"""
    try:
        ai_response = await generate_whatsapp_ai_response(msg.phone, msg.message)
        
        await db.whatsapp_conversations.insert_one({
            "phone": msg.phone,
            "user_message": msg.message,
            "ai_response": ai_response,
            "test": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"response": ai_response, "phone": msg.phone}
    except Exception as e:
        logger.error(f"WhatsApp AI error: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur IA: {str(e)}")

@api_router.get("/whatsapp/conversations")
async def get_whatsapp_conversations(current_user: dict = Depends(get_current_user)):
    result = []
    async for c in db.whatsapp_conversations.find({}).sort("created_at", -1).limit(50):
        result.append({
            "id": str(c["_id"]),
            "phone": c.get("phone", ""),
            "user_message": c.get("user_message", ""),
            "ai_response": c.get("ai_response", ""),
            "created_at": c.get("created_at", "")
        })
    return result

# ============ SETTINGS ROUTES ============
@api_router.get("/settings/notifications")
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé à l'admin")
    
    settings = await db.settings.find_one({"type": "notifications"})
    if not settings:
        return {"email_enabled": False, "notification_emails": []}
    
    return {
        "email_enabled": settings.get("email_enabled", False),
        "notification_emails": settings.get("notification_emails", [])
    }

@api_router.put("/settings/notifications")
async def update_notification_settings(settings: NotificationSettings, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé à l'admin")
    
    await db.settings.update_one(
        {"type": "notifications"},
        {"$set": {
            "type": "notifications",
            "email_enabled": settings.email_enabled,
            "notification_emails": settings.notification_emails,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"message": "Paramètres mis à jour"}

# ============ EXPORT ROUTES ============
@api_router.get("/export/clients/excel")
async def export_clients_excel(current_user: dict = Depends(get_current_user)):
    """Export clients to Excel"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Clients"
    
    # Headers
    headers = ["Nom", "Téléphone 1", "Téléphone 2", "Email", "Objectif", "Mode Paiement", "Salaire", "Budget Min", "Budget Max", "Etage Souhaité", "Situation", "Statut", "Source", "Date création"]
    ws.append(headers)
    
    # Data
    async for c in db.clients.find({}):
        ws.append([
            c.get("nom", ""),
            c.get("telephone", ""),
            c.get("telephone2", ""),
            c.get("email", ""),
            c.get("objectif", ""),
            c.get("mode_paiement", ""),
            c.get("salaire", ""),
            c.get("budget_min", ""),
            c.get("budget_max", ""),
            c.get("etage_souhaite", ""),
            c.get("situation_familiale", ""),
            c.get("statut", ""),
            c.get("source", "manual"),
            c.get("created_at", "")
        ])
    
    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=clients_{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )

@api_router.get("/export/appartements/excel")
async def export_appartements_excel(current_user: dict = Depends(get_current_user)):
    """Export apartments to Excel"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Appartements"
    
    # Get residences for mapping
    residences = {}
    async for r in db.residences.find({}):
        residences[str(r["_id"])] = r.get("nom", "")
    
    # Headers
    headers = ["Lot", "Bloc", "Résidence", "Type", "Étage", "Surface Hab. (m²)", "Surface Utile (m²)", "Prix (DA)", "Statut", "Destination"]
    ws.append(headers)
    
    # Data
    async for a in db.appartements.find({}):
        ws.append([
            a.get("numero_lot", ""),
            a.get("bloc", ""),
            residences.get(a.get("residence_id", ""), ""),
            a.get("type_appart", ""),
            a.get("etage", ""),
            a.get("surface_habitable", ""),
            a.get("surface_utile", ""),
            a.get("prix", 0),
            a.get("statut", ""),
            a.get("destination", "")
        ])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=appartements_{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )

@api_router.get("/export/clients/pdf")
async def export_clients_pdf(current_user: dict = Depends(get_current_user)):
    """Export clients to PDF"""
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1E3A5F'))
    elements.append(Paragraph("DJERBA CONSTRUCTION - Liste des Clients", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Table data
    data = [["Nom", "Téléphone", "Statut", "Température"]]
    
    async for c in db.clients.find({}):
        data.append([
            c.get("nom", "")[:20],
            c.get("telephone", ""),
            c.get("statut", ""),
            c.get("temperature", "")
        ])
    
    if len(data) > 1:
        table = Table(data, colWidths=[6*cm, 4*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A5F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        elements.append(table)
    
    doc.build(elements)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=clients_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )

# ============ USERS ROUTES (Admin only) ============
@api_router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé à l'admin")
    
    result = []
    async for u in db.users.find({}, {"password_hash": 0}):
        result.append({
            "id": str(u["_id"]),
            "email": u.get("email", ""),
            "name": u.get("name", ""),
            "role": u.get("role", "commercial"),
            "created_at": u.get("created_at", "")
        })
    return result

# ============ WEBSOCKET ============
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({"type": "message", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include router
app.include_router(api_router)

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "DJERBA CONSTRUCTION CRM API", "version": "2.0"}

# Startup event
@app.on_event("startup")
async def startup_event():
    await db.users.create_index("email", unique=True)
    
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@immo.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed,
            "name": "Administrateur",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}}
        )
        logger.info(f"Admin password updated: {admin_email}")
    
    # Seed EDIMCO residence
    residences_count = await db.residences.count_documents({})
    if residences_count == 0:
        default_residences = [
            {"nom": "EDIMCO", "adresse": "EDIMCO, Commune de Bejaia, Wilaya de Bejaia", "description": "Résidence DJERBA - 264 logements promotionnels en R+11 avec sous-sol, duplex 10e-11e étage, RDC et 1er étage commercial/service, crèche et parking souterrain", "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        await db.residences.insert_many(default_residences)
        logger.info("EDIMCO residence created")
    
    # Write test credentials
    import os as os_module
    os_module.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write(f"""# Test Credentials

## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin

## Auth Endpoints
- POST /api/auth/login
- POST /api/auth/register
- POST /api/auth/logout
- GET /api/auth/me

## WhatsApp Webhook
- GET /api/whatsapp/webhook (verification)
- POST /api/whatsapp/webhook (messages)
""")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
