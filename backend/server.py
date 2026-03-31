from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import bcrypt
import jwt
import secrets
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import asyncio
import json

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
    email: Optional[str] = None
    salaire: Optional[float] = None
    situation_familiale: Optional[str] = None
    notes: Optional[str] = None
    statut: str = "nouveau"

class ClientUpdate(BaseModel):
    nom: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    salaire: Optional[float] = None
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

class AppartementCreate(BaseModel):
    residence_id: str
    type_appart: str
    prix: float
    etage: int
    statut: str = "disponible"
    surface: Optional[float] = None
    description: Optional[str] = None

class AppartementUpdate(BaseModel):
    type_appart: Optional[str] = None
    prix: Optional[float] = None
    etage: Optional[int] = None
    statut: Optional[str] = None
    surface: Optional[float] = None
    description: Optional[str] = None
    client_id: Optional[str] = None

class WhatsAppMessage(BaseModel):
    phone: str
    message: str

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
app = FastAPI()
api_router = APIRouter(prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    
    response = JSONResponse(content={
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role
    })
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    return response

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
    
    response = JSONResponse(content={
        "id": user_id,
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user.get("role", "commercial")
    })
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    return response

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
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
        return response
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

# ============ CLIENTS ROUTES ============
@api_router.get("/clients")
async def get_clients(current_user: dict = Depends(get_current_user)):
    clients = await db.clients.find({}, {"_id": 0, "id": {"$toString": "$_id"}}).to_list(1000)
    result = []
    async for c in db.clients.find({}):
        client_data = {
            "id": str(c["_id"]),
            "nom": c.get("nom", ""),
            "telephone": c.get("telephone", ""),
            "email": c.get("email", ""),
            "salaire": c.get("salaire"),
            "situation_familiale": c.get("situation_familiale", ""),
            "notes": c.get("notes", ""),
            "statut": c.get("statut", "nouveau"),
            "appartement_id": c.get("appartement_id"),
            "created_at": c.get("created_at", ""),
            "created_by": c.get("created_by", "")
        }
        result.append(client_data)
    return result

@api_router.post("/clients")
async def create_client(client: ClientCreate, current_user: dict = Depends(get_current_user)):
    client_doc = {
        **client.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["_id"]
    }
    result = await db.clients.insert_one(client_doc)
    
    await manager.broadcast({"type": "client_created", "data": {"id": str(result.inserted_id)}})
    
    return {"id": str(result.inserted_id), **client.model_dump()}

@api_router.put("/clients/{client_id}")
async def update_client(client_id: str, client: ClientUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in client.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user["_id"]
    
    # If client status is "réservé" and has apartment_id, update apartment status
    if client.statut == "réservé" and client.appartement_id:
        await db.appartements.update_one(
            {"_id": ObjectId(client.appartement_id)},
            {"$set": {"statut": "réservé", "client_id": client_id}}
        )
    
    result = await db.clients.update_one(
        {"_id": ObjectId(client_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    await manager.broadcast({"type": "client_updated", "data": {"id": client_id}})
    
    return {"id": client_id, **update_data}

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
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
            "etage": a.get("etage", 0),
            "statut": a.get("statut", "disponible"),
            "surface": a.get("surface"),
            "description": a.get("description", ""),
            "client_id": a.get("client_id")
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
    
    # If apartment is reserved with a client, update client's apartment_id
    if appart.statut == "réservé" and appart.client_id:
        await db.clients.update_one(
            {"_id": ObjectId(appart.client_id)},
            {"$set": {"appartement_id": appart_id, "statut": "réservé"}}
        )
    
    result = await db.appartements.update_one(
        {"_id": ObjectId(appart_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appartement non trouvé")
    
    await manager.broadcast({"type": "appartement_updated", "data": {"id": appart_id}})
    
    return {"id": appart_id, **update_data}

@api_router.delete("/appartements/{appart_id}")
async def delete_appartement(appart_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.appartements.delete_one({"_id": ObjectId(appart_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appartement non trouvé")
    
    await manager.broadcast({"type": "appartement_deleted", "data": {"id": appart_id}})
    
    return {"message": "Appartement supprimé"}

# ============ DASHBOARD ROUTES ============
@api_router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    total_clients = await db.clients.count_documents({})
    total_appartements = await db.appartements.count_documents({})
    apparts_disponibles = await db.appartements.count_documents({"statut": "disponible"})
    apparts_reserves = await db.appartements.count_documents({"statut": "réservé"})
    apparts_vendus = await db.appartements.count_documents({"statut": "vendu"})
    
    # Client status breakdown
    clients_nouveau = await db.clients.count_documents({"statut": "nouveau"})
    clients_interesse = await db.clients.count_documents({"statut": "intéressé"})
    clients_visite = await db.clients.count_documents({"statut": "visite"})
    clients_reserve = await db.clients.count_documents({"statut": "réservé"})
    clients_vendu = await db.clients.count_documents({"statut": "vendu"})
    
    # Recent activities
    recent_clients = []
    async for c in db.clients.find({}).sort("created_at", -1).limit(5):
        recent_clients.append({
            "id": str(c["_id"]),
            "nom": c.get("nom", ""),
            "statut": c.get("statut", ""),
            "created_at": c.get("created_at", "")
        })
    
    return {
        "total_clients": total_clients,
        "total_appartements": total_appartements,
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
        "recent_clients": recent_clients
    }

# ============ WHATSAPP AI ROUTES ============
@api_router.post("/whatsapp/message")
async def handle_whatsapp_message(msg: WhatsAppMessage, current_user: dict = Depends(get_current_user)):
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
                "etage": a.get("etage", 0)
            })
        
        system_message = f"""Tu es un assistant immobilier professionnel pour une agence immobilière.
Tu réponds en français de manière courtoise et professionnelle.
Tu dois:
1. Répondre aux questions sur les appartements disponibles
2. Poser des questions pour qualifier le prospect (budget, type recherché, situation familiale)
3. Collecter les informations de contact

Résidences disponibles: {', '.join(residences) if residences else 'Non configurées'}
Appartements disponibles: {len(appartements)} appartements
Types: {', '.join(set(a['type'] for a in appartements)) if appartements else 'Aucun'}
Fourchette de prix: {min(a['prix'] for a in appartements) if appartements else 0}€ - {max(a['prix'] for a in appartements) if appartements else 0}€
"""
        
        chat = LlmChat(
            api_key=os.environ.get("EMERGENT_LLM_KEY"),
            session_id=f"whatsapp_{msg.phone}",
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=msg.message)
        response = await chat.send_message(user_message)
        
        # Store conversation
        await db.whatsapp_conversations.insert_one({
            "phone": msg.phone,
            "user_message": msg.message,
            "ai_response": response,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"response": response, "phone": msg.phone}
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
            # Broadcast any received message to all clients
            await manager.broadcast({"type": "message", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include router
app.include_router(api_router)

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "CRM Immobilier API"}

# Startup event - Seed admin and default residences
@app.on_event("startup")
async def startup_event():
    # Create indexes
    await db.users.create_index("email", unique=True)
    
    # Seed admin
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
    
    # Seed default residences if none exist
    residences_count = await db.residences.count_documents({})
    if residences_count == 0:
        default_residences = [
            {"nom": "Résidence A", "adresse": "", "description": "Première résidence", "created_at": datetime.now(timezone.utc).isoformat()},
            {"nom": "Résidence B", "adresse": "", "description": "Deuxième résidence", "created_at": datetime.now(timezone.utc).isoformat()},
            {"nom": "Résidence C", "adresse": "", "description": "Troisième résidence", "created_at": datetime.now(timezone.utc).isoformat()}
        ]
        await db.residences.insert_many(default_residences)
        logger.info("Default residences created")
    
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
- POST /api/auth/refresh
""")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
