from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Setting(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    setting_key = Column(String(100), nullable=False)
    setting_value = Column(Text, nullable=True)
    updated_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('guild_id', 'setting_key', name='uq_settings_guild_key'),
    )
