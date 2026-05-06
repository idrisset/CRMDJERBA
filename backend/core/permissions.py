from fastapi import HTTPException

ROLES = {
    "super_admin": {
        "label": "Super Administrateur",
        "level": 3,
        "can_manage_users": True,
        "can_delete": True,
        "can_approve": True,
        "can_modify_sensitive": True,
        "needs_approval": False,
    },
    "admin_limited": {
        "label": "Administrateur Limite",
        "level": 2,
        "can_manage_users": False,
        "can_delete": False,
        "can_approve": False,
        "can_modify_sensitive": False,
        "needs_approval": True,
    },
    "user": {
        "label": "Utilisateur",
        "level": 1,
        "can_manage_users": False,
        "can_delete": False,
        "can_approve": False,
        "can_modify_sensitive": False,
        "needs_approval": True,
    },
}

SENSITIVE_ACTIONS = ["delete_client", "delete_appartement", "delete_prospect", "modify_price", "cancel_reservation", "permanent_delete"]

def get_permissions(role: str) -> dict:
    if role == "admin":
        role = "super_admin"
    return ROLES.get(role, ROLES["user"])

def require_role(user: dict, min_level: int = 1):
    role = user.get("role", "user")
    perms = get_permissions(role)
    if perms["level"] < min_level:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    return perms
