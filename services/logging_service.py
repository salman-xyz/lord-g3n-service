from typing import Optional
from sqlalchemy.orm import Session
from database import Log
from datetime import datetime

class LoggingService:
    def __init__(self, db: Session, guild_id: int):
        self.db = db
        self.guild_id = guild_id
    
    def log(self, action: str, discord_id: int = None, staff_id: int = None, 
            ticket_id: int = None, details: str = None):
        log = Log(
            guild_id=self.guild_id,
            action=action,
            discord_id=discord_id,
            staff_id=staff_id,
            ticket_id=ticket_id,
            details=details
        )
        self.db.add(log)
        self.db.commit()
        return log
    
    def log_user_verified(self, discord_id: int, details: str = None):
        return self.log("user_verified", discord_id=discord_id, details=details)
    
    def log_user_unverified(self, discord_id: int, details: str = None):
        return self.log("user_unverified", discord_id=discord_id, details=details)
    
    def log_code_generated(self, discord_id: int, code: str, service: str, category: str):
        return self.log("code_generated", discord_id=discord_id, 
                       details=f"Code: {code}, Service: {service}, Category: {category}")
    
    def log_code_invalidated(self, discord_id: int, code: str, staff_id: int):
        return self.log("code_invalidated", discord_id=discord_id, staff_id=staff_id,
                       details=f"Code: {code}")
    
    def log_code_redeemed(self, discord_id: int, code: str, staff_id: int, ticket_id: int):
        return self.log("code_redeemed", discord_id=discord_id, staff_id=staff_id, ticket_id=ticket_id,
                       details=f"Code: {code}")
    
    def log_ticket_created(self, discord_id: int, ticket_type: str, category: str = None, service: str = None):
        return self.log("ticket_created", discord_id=discord_id,
                       details=f"Type: {ticket_type}, Category: {category}, Service: {service}")
    
    def log_ticket_deleted(self, discord_id: int, staff_id: int, ticket_id: int, reason: str,
                           category: str = None, service: str = None, created_at: datetime = None):
        details = f"Category: {category}\nService: {service}\nReason: {reason}"
        if created_at:
            details += f"\nCreated: {created_at.strftime('%d %b %Y %H:%M')}"
        details += f"\nDeleted: {datetime.utcnow().strftime('%d %b %Y %H:%M')}"
        return self.log("ticket_deleted", discord_id=discord_id, staff_id=staff_id, ticket_id=ticket_id,
                       details=details)
    
    def log_admin_action(self, staff_id: int, action: str, details: str = None):
        return self.log(action, staff_id=staff_id, details=details)
    
    def log_config_changed(self, admin_id: int, setting: str, option: str, old_value: any, new_value: any):
        return self.log("config_changed", discord_id=admin_id,
                       details=f"Setting: {setting}\nOption: {option}\nOld: {old_value}\nNew: {new_value}")
    
    def log_service_added(self, admin_id: int, service: str, category: str):
        return self.log("service_added", discord_id=admin_id,
                       details=f"Service: {service}, Category: {category}")
    
    def log_service_removed(self, admin_id: int, service: str):
        return self.log("service_removed", discord_id=admin_id,
                       details=f"Service: {service}")
    
    def log_service_enabled(self, admin_id: int, service: str):
        return self.log("service_enabled", discord_id=admin_id,
                       details=f"Service: {service}")
    
    def log_service_disabled(self, admin_id: int, service: str):
        return self.log("service_disabled", discord_id=admin_id,
                       details=f"Service: {service}")
    
    def log_google_sync(self, stats: dict):
        return self.log("google_sync", details=str(stats))
    
    def log_verification_error(self, error: str):
        return self.log("verification_error", details=error)
    
    def get_logs(self, action: str = None, limit: int = 100) -> list:
        query = self.db.query(Log).filter(Log.guild_id == self.guild_id)
        if action:
            query = query.filter(Log.action == action)
        return query.order_by(Log.created_at.desc()).limit(limit).all()


def create_log_entry(guild_id: int, action: str, discord_id: int = None, staff_id: int = None,
                     ticket_id: int = None, details: str = None):
    from database import get_db
    db = next(get_db())
    try:
        service = LoggingService(db, guild_id)
        return service.log(action, discord_id, staff_id, ticket_id, details)
    finally:
        db.close()