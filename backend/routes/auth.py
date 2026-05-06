import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Request, Depends
from bson import ObjectId
from core.database import db
from core.auth import (
    get_current_user, get_jwt_secret, verify_password, hash_password,
    create_access_token, create_refresh_token, JWT_ALGORITHM
)
from core.security import (
    get_ip_geolocation, record_login_attempt, get_failed_attempts_count,
    is_new_ip_for_user, alert_unknown_email, alert_account_locked,
    alert_new_ip_login, alert_ip_banned
)
from core.helpers import audit_log
from models.schemas import UserLogin, ChangePasswordRequest
import jwt as pyjwt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(credentials: UserLogin, request: Request):
    email = credentials.email.lower()
    ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", request.client.host if request.client else "unknown"))
    if "," in ip:
        ip = ip.split(",")[0].strip()
    user_agent = request.headers.get("User-Agent", "Inconnu")

    try:
        # CHECK 1: Is this IP banned?
        ip_ban = await db.banned_ips.find_one({"ip": ip})
        if ip_ban:
            ban_until = datetime.fromisoformat(ip_ban["banned_until"]) if isinstance(ip_ban["banned_until"], str) else ip_ban["banned_until"]
            if datetime.now(timezone.utc) < ban_until:
                remaining = int((ban_until - datetime.now(timezone.utc)).total_seconds() // 60) + 1
                raise HTTPException(status_code=403, detail=f"Adresse IP bloquee. Reessayez dans {remaining} minute(s).")
            else:
                await db.banned_ips.delete_one({"ip": ip})

        # CHECK 2: Progressive delay
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        recent_ip_failures = await db.login_attempts.count_documents({
            "ip": ip, "success": False, "timestamp": {"$gte": one_hour_ago}
        })
        if recent_ip_failures > 0:
            delay = min(recent_ip_failures * 1.0, 10.0)
            await asyncio.sleep(delay)

        # CHECK 3: IP-level ban after 10 failures
        if recent_ip_failures >= 10:
            ban_until = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            await db.banned_ips.update_one(
                {"ip": ip},
                {"$set": {"ip": ip, "banned_until": ban_until, "reason": "10+ failed login attempts", "created_at": datetime.now(timezone.utc).isoformat()}},
                upsert=True
            )
            geo = await get_ip_geolocation(ip)
            asyncio.create_task(alert_ip_banned(ip, user_agent, geo, recent_ip_failures))
            raise HTTPException(status_code=403, detail="Trop de tentatives. Adresse IP bloquee pour 1 heure.")

        user = await db.users.find_one({"email": email})

        # Case A: Unknown email
        if not user:
            await record_login_attempt(email, ip, user_agent, False)
            geo = await get_ip_geolocation(ip)
            asyncio.create_task(alert_unknown_email(email, ip, user_agent, geo))
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

        # Check if account is locked
        locked_until = user.get("locked_until")
        if locked_until:
            lock_time = datetime.fromisoformat(locked_until) if isinstance(locked_until, str) else locked_until
            if datetime.now(timezone.utc) < lock_time:
                remaining = int((lock_time - datetime.now(timezone.utc)).total_seconds() // 60) + 1
                raise HTTPException(status_code=423, detail=f"Compte bloque. Reessayez dans {remaining} minute(s).")
            else:
                await db.users.update_one({"_id": user["_id"]}, {"$unset": {"locked_until": ""}})

        # Check password
        if not verify_password(credentials.password, user["password_hash"]):
            await record_login_attempt(email, ip, user_agent, False)
            fail_count = await get_failed_attempts_count(email)

            if fail_count >= 5:
                lock_until = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
                await db.users.update_one({"_id": user["_id"]}, {"$set": {"locked_until": lock_until}})
                geo = await get_ip_geolocation(ip)
                asyncio.create_task(alert_account_locked(email, ip, user_agent, geo, fail_count))
                raise HTTPException(status_code=423, detail="Compte bloque 15 minutes apres 5 tentatives echouees.")

            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

        # Login successful
        new_ip = await is_new_ip_for_user(email, ip)
        await record_login_attempt(email, ip, user_agent, True)

        if user.get("locked_until"):
            await db.users.update_one({"_id": user["_id"]}, {"$unset": {"locked_until": ""}})

        user_id = str(user["_id"])
        access_token = create_access_token(user_id, user["email"])
        refresh_token = create_refresh_token(user_id)

        user_dict = {"_id": user_id, "name": user.get("name", ""), "email": user["email"]}
        await audit_log(user_dict, "LOGIN", "session", user_id, user.get("name", user["email"]))

        if new_ip:
            geo = await get_ip_geolocation(ip)
            asyncio.create_task(alert_new_ip_login(user["email"], ip, user_agent, geo))

        return {
            "id": user_id,
            "email": user["email"],
            "name": user.get("name", ""),
            "role": user.get("role", "commercial"),
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Login error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {type(e).__name__}: {str(e)}")


@router.post("/logout")
async def logout(request: Request):
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            payload = pyjwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
            user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
            if user:
                user_dict = {"_id": str(user["_id"]), "name": user.get("name", ""), "email": user["email"]}
                await audit_log(user_dict, "LOGOUT", "session", str(user["_id"]), user.get("name", user["email"]))
    except:
        pass
    return {"message": "Deconnexion reussie"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "name": current_user.get("name", ""),
        "role": current_user.get("role", "commercial"),
    }


@router.post("/refresh")
async def refresh_token(request: Request):
    try:
        body = await request.json()
        token = body.get("refresh_token", "")
        if not token:
            raise HTTPException(status_code=401, detail="Refresh token manquant")
        payload = pyjwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token invalide")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouve")
        new_access = create_access_token(str(user["_id"]), user["email"])
        return {"access_token": new_access}
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expire")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Refresh token invalide")


@router.put("/change-password")
async def change_password(req: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"_id": ObjectId(current_user["_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")
    if not verify_password(req.current_password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit contenir au moins 6 caracteres")
    new_hash = hash_password(req.new_password)
    await db.users.update_one({"_id": ObjectId(current_user["_id"])}, {"$set": {"password_hash": new_hash}})
    await audit_log(current_user, "UPDATE", "session", current_user["_id"], current_user.get("name", ""), new_values={"password": "***modifie***"})
    return {"message": "Mot de passe modifie avec succes"}
