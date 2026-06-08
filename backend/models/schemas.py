from pydantic import BaseModel, EmailStr
from typing import List, Optional


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "user"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class ClientCreate(BaseModel):
    nom: str
    telephone: str
    telephone2: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    salaire: Optional[float] = None
    situation_familiale: Optional[str] = None
    notes: Optional[str] = None
    statut: str = "nouveau"
    temperature: Optional[str] = "neutre"
    source: Optional[str] = None
    appartement_ids: Optional[List[str]] = None
    force_create: Optional[bool] = False

class ClientUpdate(BaseModel):
    nom: Optional[str] = None
    telephone: Optional[str] = None
    telephone2: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    salaire: Optional[float] = None
    situation_familiale: Optional[str] = None
    notes: Optional[str] = None
    statut: Optional[str] = None
    temperature: Optional[str] = None
    source: Optional[str] = None
    appartement_ids: Optional[List[str]] = None

class ApprovalRequest(BaseModel):
    action_type: str
    entity_type: str
    entity_id: str
    entity_name: str = ""
    details: dict = {}

class ResidenceCreate(BaseModel):
    nom: str
    adresse: str = ""
    description: str = ""

class ResidenceUpdate(BaseModel):
    nom: Optional[str] = None
    adresse: Optional[str] = None
    description: Optional[str] = None

class ProspectCreate(BaseModel):
    nom: str
    prenom: Optional[str] = None
    telephone: str
    telephone2: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    quartier: Optional[str] = None
    wilaya: Optional[str] = None
    profession: Optional[str] = None
    salaire: Optional[float] = None
    situation_familiale: Optional[str] = None
    nombre_enfants: Optional[int] = None
    nombre_pieces: Optional[int] = None
    type_recherche: Optional[str] = None
    type_logement: Optional[str] = None
    etage_souhaite: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    mode_paiement: Optional[str] = None
    objectif: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    statut: str = "nouveau"

class ProspectUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    telephone2: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    quartier: Optional[str] = None
    wilaya: Optional[str] = None
    profession: Optional[str] = None
    salaire: Optional[float] = None
    situation_familiale: Optional[str] = None
    nombre_enfants: Optional[int] = None
    nombre_pieces: Optional[int] = None
    type_recherche: Optional[str] = None
    type_logement: Optional[str] = None
    etage_souhaite: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    mode_paiement: Optional[str] = None
    objectif: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    statut: Optional[str] = None

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

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class BackupEmailSettings(BaseModel):
    enabled: bool
    email: str = ""
