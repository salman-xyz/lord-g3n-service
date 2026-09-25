from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Index
from sqlalchemy.sql import func
from database import Base

class Code(Base):
    __tablename__ = 'codes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    code = Column(String(20), nullable=False, index=True)
    discord_id = Column(BigInteger, nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=True)
    service_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    generator_type = Column(String(50), nullable=False)
    status = Column(String(20), default='unused')
    created_at = Column(DateTime, server_default=func.now())
    activated_at = Column(DateTime, nullable=True)
    redeemed_at = Column(DateTime, nullable=True)
    redeemed_by = Column(BigInteger, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('ix_codes_guild_code', 'guild_id', 'code'),
        Index('ix_codes_guild_discord_status', 'guild_id', 'discord_id', 'status'),
    )
