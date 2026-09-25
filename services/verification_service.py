from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database import User, VerificationSubmission, Log
from config import GOOGLE_FORM_URL
from services.google_sheets import GoogleSheetsService

class VerificationService:
    def __init__(self, db: Session, guild_id: int):
        self.db = db
        self.guild_id = guild_id
        self.sheets_service = GoogleSheetsService(db, guild_id)
    
    def is_verified(self, discord_id: int) -> bool:
        user = self.db.query(User).filter(
            User.guild_id == self.guild_id,
            User.discord_id == discord_id
        ).first()
        return user.verified if user else False
    
    async def is_verified_async(self, discord_id: int, username: str = None) -> bool:
        """Check verification - once verified, stays verified, no re-sync needed"""
        from database import get_db
        from services.google_sheets import GoogleSheetsService
        
        # First check with a fresh session
        db = next(get_db())
        try:
            user = db.query(User).filter(
                User.guild_id == self.guild_id,
                User.discord_id == discord_id
            ).first()
            if user and user.verified:
                return True
        finally:
            db.close()
        
        # Not verified in DB - sync from Google Sheets with fresh session
        try:
            fresh_db = next(get_db())
            try:
                fresh_service = GoogleSheetsService(fresh_db, self.guild_id)
                await fresh_service.sync_verifications()
            finally:
                fresh_db.close()
        except Exception as e:
            print(f"Auto-sync failed: {e}")
        
        # Re-check with fresh session
        db = next(get_db())
        try:
            user = db.query(User).filter(
                User.guild_id == self.guild_id,
                User.discord_id == discord_id
            ).first()
            if user and user.verified:
                return True
            return False
        finally:
            db.close()
    
    def get_user(self, discord_id: int) -> Optional[User]:
        return self.db.query(User).filter(
            User.guild_id == self.guild_id,
            User.discord_id == discord_id
        ).first()
    
    def verify_user(self, discord_id: int, username: str) -> bool:
        user = self.get_user(discord_id)
        if user:
            user.verified = True
            user.verified_at = __import__('datetime').datetime.utcnow()
            user.discord_username = username
        else:
            user = User(
                guild_id=self.guild_id,
                discord_id=discord_id,
                discord_username=username,
                verified=True,
                verified_at=__import__('datetime').datetime.utcnow()
            )
            self.db.add(user)
        
        log = Log(
            guild_id=self.guild_id,
            action="user_verified",
            discord_id=discord_id,
            details=f"Manually verified"
        )
        self.db.add(log)
        self.db.commit()
        return True
    
    def unverify_user(self, discord_id: int) -> bool:
        user = self.get_user(discord_id)
        if user:
            user.verified = False
            user.verified_at = None
            log = Log(
                guild_id=self.guild_id,
                action="user_unverified",
                discord_id=discord_id,
                details=f"Manually unverified"
            )
            self.db.add(log)
            self.db.commit()
            return True
        return False
    
    async def check_verification(self, discord_id: int, username: str) -> Dict[str, Any]:
        user = self.get_user(discord_id)
        if user and user.verified:
            return {
                "verified": True,
                "discord_id": user.discord_id,
                "username": user.discord_username,
                "verified_at": user.verified_at.isoformat() if user.verified_at else None
            }
        
        stats = await self.sheets_service.sync_verifications()
        
        user = self.get_user(discord_id)
        if user and user.verified:
            return {
                "verified": True,
                "discord_id": user.discord_id,
                "username": user.discord_username,
                "verified_at": user.verified_at.isoformat() if user.verified_at else None
            }
        
        return {
            "verified": False,
            "discord_id": discord_id,
            "username": username,
            "sync_stats": stats
        }
    
    async def manual_sync(self) -> Dict[str, int]:
        return await self.sheets_service.sync_verifications()
    
    def get_verification_stats(self) -> Dict[str, int]:
        total = self.db.query(User).filter(User.guild_id == self.guild_id).count()
        verified = self.db.query(User).filter(
            User.guild_id == self.guild_id,
            User.verified == True
        ).count()
        return {"total": total, "verified": verified, "unverified": total - verified}

    def get_user_stats(self) -> Dict[str, int]:
        return self.get_verification_stats()
    
    def get_form_url(self) -> str:
        from config import GOOGLE_FORM_URL
        return GOOGLE_FORM_URL or "https://forms.google.com"


async def check_verification(guild_id: int, discord_id: int, username: str) -> dict:
    from database import get_db
    db = next(get_db())
    try:
        service = VerificationService(db, guild_id)
        return await service.check_verification(discord_id, username)
    finally:
        db.close()


def unverify_user(guild_id: int, discord_id: int) -> bool:
    from database import get_db
    db = next(get_db())
    try:
        service = VerificationService(db, guild_id)
        return service.unverify_user(discord_id)
    finally:
        db.close()


def get_user_stats(guild_id: int) -> dict:
    from database import get_db
    db = next(get_db())
    try:
        service = VerificationService(db, guild_id)
        return service.get_user_stats()
    finally:
        db.close()


def get_user_by_discord_id(guild_id: int, discord_id: int):
    from database import get_db
    db = next(get_db())
    try:
        service = VerificationService(db, guild_id)
        return service.get_user(discord_id)
    finally:
        db.close()


def get_or_create_user(guild_id: int, discord_id: int, username: str = None):
    from database import get_db, User
    from datetime import datetime
    db = next(get_db())
    try:
        user = db.query(User).filter(
            User.guild_id == guild_id,
            User.discord_id == discord_id
        ).first()
        if user:
            if username:
                user.discord_username = username
                db.commit()
            return user
        user = User(
            guild_id=guild_id,
            discord_id=discord_id,
            discord_username=username or f"User_{discord_id}",
            verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()