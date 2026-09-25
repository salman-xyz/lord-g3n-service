import random
import string
from typing import Optional, List
from sqlalchemy.orm import Session
from database import Code, Service
from config import CODE_LENGTH

class CodeGenerator:
    def __init__(self, db: Session, guild_id: int):
        self.db = db
        self.guild_id = guild_id
        self._code_length = None
        self._chars = string.ascii_letters + string.digits
    
    def _get_code_length(self) -> int:
        if self._code_length is None:
            from config import DEFAULT_SETTINGS
            self._code_length = DEFAULT_SETTINGS.get("free_gen_code_length", CODE_LENGTH)
        return self._code_length
    
    def generate_code(self, length: int = None) -> str:
        length = length or self._get_code_length()
        return ''.join(random.choices(self._chars, k=length))
    
    def generate_unique_code(self, max_attempts: int = 100) -> Optional[str]:
        for _ in range(max_attempts):
            code = self.generate_code()
            existing = self.db.query(Code).filter(
                Code.guild_id == self.guild_id,
                Code.code == code
            ).first()
            if not existing:
                return code
        return None
    
    def create_code(self, discord_id: int, service: Service, category: str, generator_type: str, code: str = None) -> Code:
        if code is None:
            code = self.generate_unique_code()
            if code is None:
                raise ValueError("Failed to generate unique code")
        
        new_code = Code(
            guild_id=self.guild_id,
            code=code,
            discord_id=discord_id,
            service_id=service.id,
            category=category,
            generator_type=generator_type,
            status="unused"
        )
        self.db.add(new_code)
        self.db.commit()
        self.db.refresh(new_code)
        return new_code
    
    def get_user_codes(self, discord_id: int, status: str = "unused") -> List[Code]:
        return self.db.query(Code).filter(
            Code.guild_id == self.guild_id,
            Code.discord_id == discord_id,
            Code.status == status
        ).all()
    
    def get_code_by_value(self, code: str) -> Optional[Code]:
        from sqlalchemy import func
        return self.db.query(Code).filter(
            Code.guild_id == self.guild_id,
            func.upper(Code.code) == code.upper()
        ).first()
    
    def invalidate_code(self, code_id: int) -> bool:
        code = self.db.query(Code).filter(
            Code.guild_id == self.guild_id,
            Code.id == code_id
        ).first()
        if code:
            code.status = "invalidated"
            self.db.commit()
            return True
        return False


def get_code_by_value(guild_id: int, code_value: str):
    from database import get_db
    db = next(get_db())
    try:
        generator = CodeGenerator(db, guild_id)
        return generator.get_code_by_value(code_value)
    finally:
        db.close()


def invalidate_code(guild_id: int, code_id: int) -> bool:
    from database import get_db
    db = next(get_db())
    try:
        generator = CodeGenerator(db, guild_id)
        return generator.invalidate_code(code_id)
    finally:
        db.close()


def get_code_stats(guild_id: int) -> dict:
    from database import get_db, Code
    db = next(get_db())
    try:
        total = db.query(Code).filter(Code.guild_id == guild_id).count()
        unused = db.query(Code).filter(Code.guild_id == guild_id, Code.status == "unused").count()
        redeemed = db.query(Code).filter(Code.guild_id == guild_id, Code.status == "redeemed").count()
        expired = db.query(Code).filter(Code.guild_id == guild_id, Code.status == "expired").count()
        invalidated = db.query(Code).filter(Code.guild_id == guild_id, Code.status == "invalidated").count()
        return {
            "total": total,
            "unused": unused,
            "redeemed": redeemed,
            "expired": expired,
            "invalidated": invalidated
        }
    finally:
        db.close()


def create_code(guild_id: int, discord_id: int, service, category: str, generator_type: str, code_length: int = 5):
    from database import get_db
    db = next(get_db())
    try:
        generator = CodeGenerator(db, guild_id)
        code_str = generator.generate_unique_code()
        if code_str is None:
            raise ValueError("Failed to generate unique code")
        return generator.create_code(discord_id, service, category, generator_type, code_str)
    finally:
        db.close()