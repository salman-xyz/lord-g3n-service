import discord
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from database import Ticket, Code, User, Log, Setting
from config import TICKET_TYPES, MAX_ACTIVE_TICKETS

class TicketService:
    def __init__(self, db: Session, guild_id: int):
        self.db = db
        self.guild_id = guild_id
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        setting = self.db.query(Setting).filter(
            Setting.guild_id == self.guild_id,
            Setting.setting_key == key
        ).first()
        if setting:
            try:
                import json
                return json.loads(setting.setting_value)
            except (json.JSONDecodeError, TypeError):
                return setting.setting_value
        return default
    
    def get_active_tickets(self, discord_id: int) -> List[Ticket]:
        return self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.discord_id == discord_id,
            Ticket.status == "open"
        ).all()
    
    def get_active_ticket_count(self, discord_id: int, guild=None) -> int:
        tickets = self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.discord_id == discord_id,
            Ticket.status == "open"
        ).all()
        
        if guild:
            # Filter out tickets with deleted channels
            count = 0
            for ticket in tickets:
                if guild.get_channel(ticket.channel_id):
                    count += 1
            return count
        return len(tickets)
    
    def has_active_ticket(self, discord_id: int, guild=None) -> bool:
        return self.get_active_ticket_count(discord_id, guild) > 0
    
    def get_max_active_tickets(self) -> int:
        return self.get_setting("max_active_tickets", MAX_ACTIVE_TICKETS)
    
    def can_create_ticket(self, discord_id: int, guild=None) -> tuple[bool, str]:
        max_tickets = self.get_max_active_tickets()
        active_count = self.get_active_ticket_count(discord_id, guild)
        if active_count >= max_tickets:
            return False, f"You already have {active_count} active ticket(s). Maximum allowed: {max_tickets}."
        return True, ""
    
    def create_ticket(self, channel_id: int, discord_id: int, ticket_type: str, 
                      category: str = None, service: str = None, code_id: int = None) -> Ticket:
        ticket = Ticket(
            guild_id=self.guild_id,
            channel_id=channel_id,
            discord_id=discord_id,
            ticket_type=ticket_type,
            category=category,
            service=service,
            code_id=code_id,
            status="open"
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket
    
    def get_ticket_by_channel(self, channel_id: int) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.channel_id == channel_id
        ).first()
    
    def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.id == ticket_id
        ).first()
    
    def close_ticket(self, ticket_id: int, deleted_by: int, reason: str) -> Optional[Ticket]:
        ticket = self.get_ticket(ticket_id)
        if ticket:
            from datetime import datetime
            ticket.status = "closed"
            ticket.closed_at = datetime.utcnow()
            ticket.deleted_by = deleted_by
            ticket.delete_reason = reason
            self.db.commit()
        return ticket
    
    def redeem_code_in_ticket(self, ticket_id: int, staff_id: int) -> tuple[bool, str]:
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False, "Ticket not found"
        
        if ticket.ticket_type != "redeem":
            return False, "This is not a redeem ticket"
        
        if not ticket.code_id:
            return False, "No code associated with this ticket"
        
        code = self.db.query(Code).filter(
            Code.guild_id == self.guild_id,
            Code.id == ticket.code_id
        ).first()
        
        if not code:
            return False, "Code not found"
        
        if code.status != "unused":
            return False, f"Code is already {code.status}"
        
        if code.discord_id != ticket.discord_id:
            return False, "Code does not belong to ticket owner"
        
        from datetime import datetime
        code.status = "redeemed"
        code.redeemed_at = datetime.utcnow()
        code.redeemed_by = staff_id
        
        log = Log(
            guild_id=self.guild_id,
            action="code_redeemed",
            discord_id=ticket.discord_id,
            staff_id=staff_id,
            ticket_id=ticket.id,
            details=f"Code {code.code} for {code.category}/{code.service.name if code.service else 'Unknown'} redeemed"
        )
        self.db.add(log)
        self.db.commit()
        
        return True, f"Code {code.code} redeemed successfully"
    
    def get_ticket_category_id(self, ticket_type: str) -> Optional[int]:
        category_map = {
            "redeem": "redeem_ticket_category_id",
            "reward": "reward_ticket_category_id",
            "purchase": "purchase_ticket_category_id",
            "report": "report_ticket_category_id",
            "partnership": "partnership_ticket_category_id",
            "support": "support_ticket_category_id"
        }
        key = category_map.get(ticket_type)
        if key:
            return self.get_setting(key)
        return None
    
    def get_ticket_name_format(self) -> str:
        return self.get_setting("ticket_name_format", "{type}-{username}")
    
    def get_welcome_message(self) -> str:
        return self.get_setting("ticket_welcome_message", 
            "Welcome {user_mention},\n\n**Please wait until our support team assists you shortly.**\n\n**Category**\n{category}\n\n**Service**\n{service}\n\nPowered by Lord G3N Services")
    
    def is_delete_reason_required(self) -> bool:
        return self.get_setting("delete_reason_required", True)
    
    def get_auto_delete_delay(self) -> int:
        return self.get_setting("auto_delete_delay", 5)
    
    def log_ticket_action(self, action: str, discord_id: int, staff_id: int = None, 
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
    
    def get_ticket_stats(self) -> dict:
        open_tickets = self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.status == "open"
        ).count()
        closed_tickets = self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.status == "closed"
        ).count()
        redeem_tickets = self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.ticket_type == "redeem"
        ).count()
        rewards_tickets = self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.ticket_type == "rewards"
        ).count()
        support_tickets = self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.ticket_type == "support"
        ).count()
        return {
            "total": open_tickets + closed_tickets,
            "open": open_tickets,
            "closed": closed_tickets,
            "by_type": {
                "redeem": redeem_tickets,
                "rewards": rewards_tickets,
                "support": support_tickets
            }
        }

    def get_ticket_log_channel_id(self) -> Optional[int]:
        return self.get_setting("ticket_log_channel_id")
    
    def get_staff_role_id(self) -> Optional[int]:
        return self.get_setting("ticket_staff_role_id")

from typing import Any


def get_ticket_stats(guild_id: int) -> dict:
    from database import get_db
    db = next(get_db())
    try:
        service = TicketService(db, guild_id)
        return service.get_ticket_stats()
    finally:
        db.close()