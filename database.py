from sqlalchemy import (
    create_engine, Column, Integer, String, BigInteger, Boolean, DateTime, 
    Text, ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import os
from config import BASE_DIR

Base = declarative_base()

engine = create_engine(f"sqlite:///{BASE_DIR / 'data' / 'database.sqlite'}", echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    discord_id = Column(BigInteger, nullable=False, index=True)
    discord_username = Column(String(255), nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('guild_id', 'discord_id', name='uq_user_guild_discord'),
        Index('ix_user_guild_verified', 'guild_id', 'verified'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "discord_id": self.discord_id,
            "discord_username": self.discord_username,
            "verified": self.verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('guild_id', 'name', name='uq_service_guild_name'),
        Index('ix_service_guild_category', 'guild_id', 'category'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "name": self.name,
            "category": self.category,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Code(Base):
    __tablename__ = "codes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    code = Column(String(100), nullable=False, index=True)
    discord_id = Column(BigInteger, nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    category = Column(String(100), nullable=False)
    generator_type = Column(String(50), nullable=False)
    status = Column(String(50), default="unused", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    activated_at = Column(DateTime, nullable=True)
    redeemed_at = Column(DateTime, nullable=True)
    redeemed_by = Column(BigInteger, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('guild_id', 'code', name='uq_code_guild_code'),
        Index('ix_code_guild_status', 'guild_id', 'status'),
        Index('ix_code_discord_status', 'discord_id', 'status'),
    )
    
    service = relationship("Service")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "code": self.code,
            "discord_id": self.discord_id,
            "service_id": self.service_id,
            "service_name": self.service.name if self.service else None,
            "category": self.category,
            "generator_type": self.generator_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "redeemed_at": self.redeemed_at.isoformat() if self.redeemed_at else None,
            "redeemed_by": self.redeemed_by,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    channel_id = Column(BigInteger, nullable=False, unique=True)
    discord_id = Column(BigInteger, nullable=False, index=True)
    ticket_type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=True)
    service = Column(String(255), nullable=True)
    code_id = Column(Integer, ForeignKey("codes.id"), nullable=True)
    status = Column(String(50), default="open", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    deleted_by = Column(BigInteger, nullable=True)
    delete_reason = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('ix_ticket_guild_status', 'guild_id', 'status'),
        Index('ix_ticket_discord_status', 'discord_id', 'status'),
    )
    
    code = relationship("Code")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "discord_id": self.discord_id,
            "ticket_type": self.ticket_type,
            "category": self.category,
            "service": self.service,
            "code_id": self.code_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "deleted_by": self.deleted_by,
            "delete_reason": self.delete_reason,
        }

class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    setting_key = Column(String(255), nullable=False)
    setting_value = Column(Text, nullable=True)
    updated_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('guild_id', 'setting_key', name='uq_setting_guild_key'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "setting_key": self.setting_key,
            "setting_value": self.setting_value,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class VerificationSubmission(Base):
    __tablename__ = "verification_submissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    sheet_row_number = Column(Integer, nullable=False)
    timestamp = Column(String(100), nullable=True)
    discord_username = Column(String(255), nullable=True)
    discord_id = Column(BigInteger, nullable=True, index=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    error = Column(Text, nullable=True)
    used = Column(Boolean, default=False, nullable=False)
    used_for_ticket_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('guild_id', 'sheet_row_number', name='uq_verification_guild_row'),
        Index('ix_verification_guild_discord', 'guild_id', 'discord_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "sheet_row_number": self.sheet_row_number,
            "timestamp": self.timestamp,
            "discord_username": self.discord_username,
            "discord_id": self.discord_id,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "status": self.status,
            "error": self.error,
            "used": self.used,
            "used_for_ticket_id": self.used_for_ticket_id,
        }

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    discord_id = Column(BigInteger, nullable=True, index=True)
    staff_id = Column(BigInteger, nullable=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('ix_log_guild_action', 'guild_id', 'action'),
        Index('ix_log_guild_created', 'guild_id', 'created_at'),
    )
    
    ticket = relationship("Ticket")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "action": self.action,
            "discord_id": self.discord_id,
            "staff_id": self.staff_id,
            "ticket_id": self.ticket_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class GuildSettings:
    def __init__(self, db: Session, guild_id: int):
        self.db = db
        self.guild_id = guild_id
        self._cache: Dict[str, Any] = {}
        self._loaded = False
    
    def _load_all(self):
        if self._loaded:
            return
        settings = self.db.query(Setting).filter(Setting.guild_id == self.guild_id).all()
        for s in settings:
            try:
                self._cache[s.setting_key] = json.loads(s.setting_value)
            except (json.JSONDecodeError, TypeError):
                self._cache[s.setting_key] = s.setting_value
        self._loaded = True
    
    def get(self, key: str, default: Any = None) -> Any:
        self._load_all()
        if key in self._cache:
            return self._cache[key]
        from config import DEFAULT_SETTINGS
        return DEFAULT_SETTINGS.get(key, default)
    
    def set(self, key: str, value: Any, updated_by: int = None):
        self._load_all()
        old_value = self._cache.get(key)
        self._cache[key] = value
        
        setting = self.db.query(Setting).filter(
            Setting.guild_id == self.guild_id,
            Setting.setting_key == key
        ).first()
        
        if setting:
            setting.setting_value = json.dumps(value) if not isinstance(value, (str, int, float, bool, type(None))) else str(value)
            setting.updated_by = updated_by
            setting.updated_at = datetime.utcnow()
        else:
            setting = Setting(
                guild_id=self.guild_id,
                setting_key=key,
                setting_value=json.dumps(value) if not isinstance(value, (str, int, float, bool, type(None))) else str(value),
                updated_by=updated_by
            )
            self.db.add(setting)
        
        self.db.commit()
        return old_value
    
    def get_all(self) -> Dict[str, Any]:
        self._load_all()
        return self._cache.copy()
    
    def reset(self, key: str, updated_by: int = None) -> Any:
        from config import DEFAULT_SETTINGS
        default = DEFAULT_SETTINGS.get(key)
        if default is not None:
            return self.set(key, default, updated_by)
        return None

def get_guild_settings(db: Session, guild_id: int) -> GuildSettings:
    return GuildSettings(db, guild_id)