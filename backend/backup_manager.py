"""
Backup & Restore system for DJERBA CONSTRUCTION CRM.
Uses mongodump/mongorestore for reliable MongoDB backups.
Supports automatic scheduling (every 6h), manual backups, restore, and retention policies.
"""
import os
import asyncio
import subprocess
import shutil
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger("backup")

BACKUP_DIR = os.environ.get("BACKUP_DIR", "/app/backups")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

# Retention policy
RETENTION_DAILY = 7       # Keep 7 daily backups
RETENTION_WEEKLY = 4      # Keep 4 weekly backups
RETENTION_MONTHLY = 3     # Keep 3 monthly backups

# Collections to backup
COLLECTIONS = [
    "clients", "appartements", "prospects", "reservations",
    "audit_logs", "approval_requests", "users", "residences",
    "notification_settings", "whatsapp_messages", "backups"
]


def get_backup_path(backup_id: str) -> str:
    return os.path.join(BACKUP_DIR, backup_id)


async def create_backup(backup_type: str = "manual", triggered_by: str = "system") -> dict:
    """Create a MongoDB backup using mongodump. Runs in a thread to avoid blocking."""
    ts = datetime.now(timezone.utc)
    backup_id = f"backup_{ts.strftime('%Y%m%d_%H%M%S')}_{backup_type}"
    backup_path = get_backup_path(backup_id)
    
    meta = {
        "backup_id": backup_id,
        "type": backup_type,
        "triggered_by": triggered_by,
        "status": "in_progress",
        "created_at": ts.isoformat(),
        "size_mb": 0,
        "collections": COLLECTIONS,
        "error": None,
    }
    
    try:
        os.makedirs(backup_path, exist_ok=True)
        
        # Run mongodump in a thread to not block the event loop
        cmd = [
            "mongodump",
            f"--uri={MONGO_URL}",
            f"--db={DB_NAME}",
            f"--out={backup_path}",
            "--quiet"
        ]
        
        result = await asyncio.to_thread(
            subprocess.run, cmd,
            capture_output=True, text=True, timeout=300
        )
        
        if result.returncode != 0:
            raise Exception(f"mongodump failed: {result.stderr}")
        
        # Calculate backup size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(backup_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        
        meta["status"] = "success"
        meta["size_mb"] = round(total_size / (1024 * 1024), 2)
        meta["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Count documents per collection
        doc_counts = {}
        db_path = os.path.join(backup_path, DB_NAME)
        if os.path.isdir(db_path):
            for f in os.listdir(db_path):
                if f.endswith(".bson"):
                    col_name = f.replace(".bson", "")
                    fsize = os.path.getsize(os.path.join(db_path, f))
                    doc_counts[col_name] = f"{round(fsize / 1024, 1)} KB"
        meta["collection_sizes"] = doc_counts
        
        logger.info(f"Backup created: {backup_id} ({meta['size_mb']} MB)")
        
    except Exception as e:
        meta["status"] = "failed"
        meta["error"] = str(e)
        meta["completed_at"] = datetime.now(timezone.utc).isoformat()
        logger.error(f"Backup failed: {backup_id} - {e}")
        # Clean up failed backup
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path, ignore_errors=True)
    
    # Save metadata
    meta_path = os.path.join(BACKUP_DIR, f"{backup_id}.json")
    try:
        with open(meta_path, "w") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    
    return meta


async def restore_backup(backup_id: str) -> dict:
    """Restore a MongoDB backup using mongorestore."""
    backup_path = get_backup_path(backup_id)
    db_path = os.path.join(backup_path, DB_NAME)
    
    if not os.path.isdir(db_path):
        return {"status": "failed", "error": f"Backup not found: {backup_id}"}
    
    try:
        cmd = [
            "mongorestore",
            f"--uri={MONGO_URL}",
            f"--db={DB_NAME}",
            f"--dir={db_path}",
            "--drop",
            "--quiet"
        ]
        
        result = await asyncio.to_thread(
            subprocess.run, cmd,
            capture_output=True, text=True, timeout=300
        )
        
        if result.returncode != 0:
            raise Exception(f"mongorestore failed: {result.stderr}")
        
        logger.info(f"Backup restored: {backup_id}")
        return {
            "status": "success",
            "backup_id": backup_id,
            "restored_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Restore failed: {backup_id} - {e}")
        return {"status": "failed", "error": str(e)}


def list_backups() -> list:
    """List all available backups from metadata files."""
    backups = []
    if not os.path.isdir(BACKUP_DIR):
        return backups
    
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.endswith(".json") and f.startswith("backup_"):
            try:
                with open(os.path.join(BACKUP_DIR, f)) as fh:
                    meta = json.load(fh)
                    # Verify the actual backup data still exists
                    bp = get_backup_path(meta["backup_id"])
                    meta["exists"] = os.path.isdir(bp)
                    backups.append(meta)
            except Exception:
                pass
    
    return backups


def delete_backup(backup_id: str) -> bool:
    """Delete a backup and its metadata."""
    backup_path = get_backup_path(backup_id)
    meta_path = os.path.join(BACKUP_DIR, f"{backup_id}.json")
    
    deleted = False
    if os.path.isdir(backup_path):
        shutil.rmtree(backup_path, ignore_errors=True)
        deleted = True
    if os.path.exists(meta_path):
        os.remove(meta_path)
        deleted = True
    
    return deleted


async def apply_retention_policy():
    """Apply retention policy: keep 7 daily, 4 weekly, 3 monthly."""
    backups = list_backups()
    if not backups:
        return
    
    now = datetime.now(timezone.utc)
    to_keep = set()
    to_delete = []
    
    # Sort by creation time
    for b in backups:
        try:
            b["_dt"] = datetime.fromisoformat(b["created_at"])
        except Exception:
            b["_dt"] = now
    
    backups.sort(key=lambda x: x["_dt"], reverse=True)
    
    # Keep last 7 daily backups (latest per day)
    daily_seen = set()
    for b in backups:
        day_key = b["_dt"].strftime("%Y-%m-%d")
        if day_key not in daily_seen and len(daily_seen) < RETENTION_DAILY:
            daily_seen.add(day_key)
            to_keep.add(b["backup_id"])
    
    # Keep last 4 weekly backups (latest per week)
    weekly_seen = set()
    for b in backups:
        week_key = b["_dt"].strftime("%Y-W%W")
        if week_key not in weekly_seen and len(weekly_seen) < RETENTION_WEEKLY:
            weekly_seen.add(week_key)
            to_keep.add(b["backup_id"])
    
    # Keep last 3 monthly backups (latest per month)
    monthly_seen = set()
    for b in backups:
        month_key = b["_dt"].strftime("%Y-%m")
        if month_key not in monthly_seen and len(monthly_seen) < RETENTION_MONTHLY:
            monthly_seen.add(month_key)
            to_keep.add(b["backup_id"])
    
    # Always keep manual backups less than 30 days old
    for b in backups:
        if b.get("type") == "manual" and (now - b["_dt"]).days < 30:
            to_keep.add(b["backup_id"])
    
    # Delete old backups not in keep set
    for b in backups:
        if b["backup_id"] not in to_keep and b.get("status") == "success":
            age_days = (now - b["_dt"]).days
            if age_days > 7:  # Never delete backups less than 7 days old
                delete_backup(b["backup_id"])
                to_delete.append(b["backup_id"])
    
    if to_delete:
        logger.info(f"Retention: deleted {len(to_delete)} old backups")
