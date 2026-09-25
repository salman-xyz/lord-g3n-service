from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text
from sqlalchemy.sql import func
from database import Base

class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False)
    channel_id = Column(BigInteger, nullable=True)
    discord_id = Column(BigInteger, nullable=False)
    ticket_type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    service = Column(String(100), nullable=True)
    code_id = Column(Integer, nullable=True)
    status = Column(String(20), default='open')
    created_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)
    deleted_by = Column(BigInteger, nullable=True)
    delete_reason = Column(Text, nullable=True)
