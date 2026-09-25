from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, UniqueConstraint, Boolean
from sqlalchemy.sql import func
from database import Base

class VerificationSubmission(Base):
    __tablename__ = 'verification_submissions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False)
    sheet_row_number = Column(Integer, nullable=False)
    timestamp = Column(String(200), nullable=True)
    discord_username = Column(String(100), nullable=True)
    discord_id = Column(BigInteger, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default='pending')
    error = Column(Text, nullable=True)
    used = Column(Boolean, default=False)
    used_for_ticket_id = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('guild_id', 'sheet_row_number', name='uq_verification_guild_row'),
    )

class Log(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    action = Column(String(100), nullable=False)
    discord_id = Column(BigInteger, nullable=True)
    staff_id = Column(BigInteger, nullable=True)
    ticket_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
