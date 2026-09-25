from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    discord_id = Column(BigInteger, nullable=False, index=True)
    discord_username = Column(String(100))
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('guild_id', 'discord_id', name='uq_user_guild_discord'),
    )
