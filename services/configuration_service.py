import discord
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from database import Service, Setting, User, Code, Ticket, Log
from config import DEFAULT_SETTINGS, GENERATOR_TIERS, GENERATOR_TIER_DISPLAY, TICKET_TYPES, PANEL_CATEGORIES

class ConfigurationService:
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
        return DEFAULT_SETTINGS.get(key, default)
    
    def set_setting(self, key: str, value: Any, updated_by: int = None) -> Any:
        old_value = self.get_setting(key)
        
        setting = self.db.query(Setting).filter(
            Setting.guild_id == self.guild_id,
            Setting.setting_key == key
        ).first()
        
        import json
        if isinstance(value, (dict, list)):
            str_value = json.dumps(value)
        elif isinstance(value, bool):
            str_value = "true" if value else "false"
        else:
            str_value = str(value) if value is not None else ""
        
        if setting:
            setting.setting_value = str_value
            setting.updated_by = updated_by
            from datetime import datetime
            setting.updated_at = datetime.utcnow()
        else:
            setting = Setting(
                guild_id=self.guild_id,
                setting_key=key,
                setting_value=str_value,
                updated_by=updated_by
            )
            self.db.add(setting)
        
        self.db.commit()
        return old_value
    
    def reset_setting(self, key: str, updated_by: int = None) -> Any:
        default = DEFAULT_SETTINGS.get(key)
        if default is not None:
            return self.set_setting(key, default, updated_by)
        return None
    
    def get_all_settings(self) -> Dict[str, Any]:
        settings = self.db.query(Setting).filter(Setting.guild_id == self.guild_id).all()
        result = {}
        import json
        for s in settings:
            try:
                result[s.setting_key] = json.loads(s.setting_value)
            except (json.JSONDecodeError, TypeError):
                result[s.setting_key] = s.setting_value
        for key, default in DEFAULT_SETTINGS.items():
            if key not in result:
                result[key] = default
        return result
    
    def get_generator_settings(self, tier: str) -> Dict[str, Any]:
        prefix = f"{tier}_gen_"
        settings = {}
        for key, default in DEFAULT_SETTINGS.items():
            if key.startswith(prefix):
                settings[key] = self.get_setting(key, default)
        return settings
    
    def get_ticket_settings(self) -> Dict[str, Any]:
        ticket_keys = [k for k in DEFAULT_SETTINGS.keys() if k.startswith("ticket_") or k.startswith("redeem_ticket_") or k.startswith("rewards_ticket_") or k.startswith("support_ticket_") or k in ["max_active_tickets", "ticket_name_format", "ticket_welcome_message", "delete_reason_required", "auto_delete_delay"]]
        return {k: self.get_setting(k, DEFAULT_SETTINGS[k]) for k in ticket_keys}
    
    def add_service(self, category: str, name: str) -> Tuple[bool, str]:
        existing = self.db.query(Service).filter(
            Service.guild_id == self.guild_id,
            Service.name == name.lower()
        ).first()
        if existing:
            return False, f"Service '{name}' already exists"
        
        service = Service(
            guild_id=self.guild_id,
            name=name.lower(),
            category=category.lower(),
            enabled=True
        )
        self.db.add(service)
        self.db.commit()
        
        tier_services_key = f"{category}_gen_services"
        if tier_services_key in DEFAULT_SETTINGS:
            current = self.get_setting(tier_services_key, [])
            if name.lower() not in current:
                current.append(name.lower())
                self.set_setting(tier_services_key, current)
        
        return True, f"Service '{name}' added to category '{category}'"
    
    def remove_service(self, name: str) -> Tuple[bool, str]:
        service = self.db.query(Service).filter(
            Service.guild_id == self.guild_id,
            Service.name == name.lower()
        ).first()
        if not service:
            return False, f"Service '{name}' not found"
        
        category = service.category
        self.db.delete(service)
        self.db.commit()
        
        tier_services_key = f"{category}_gen_services"
        if tier_services_key in DEFAULT_SETTINGS:
            current = self.get_setting(tier_services_key, [])
            if name.lower() in current:
                current.remove(name.lower())
                self.set_setting(tier_services_key, current)
        
        return True, f"Service '{name}' removed"
    
    def enable_service(self, name: str) -> Tuple[bool, str]:
        service = self.db.query(Service).filter(
            Service.guild_id == self.guild_id,
            Service.name == name.lower()
        ).first()
        if not service:
            return False, f"Service '{name}' not found"
        service.enabled = True
        self.db.commit()
        return True, f"Service '{name}' enabled"
    
    def disable_service(self, name: str) -> Tuple[bool, str]:
        service = self.db.query(Service).filter(
            Service.guild_id == self.guild_id,
            Service.name == name.lower()
        ).first()
        if not service:
            return False, f"Service '{name}' not found"
        service.enabled = False
        self.db.commit()
        return True, f"Service '{name}' disabled"
    
    def get_services(self, category: str = None) -> List[Service]:
        query = self.db.query(Service).filter(Service.guild_id == self.guild_id)
        if category:
            query = query.filter(Service.category == category.lower())
        return query.order_by(Service.category, Service.name).all()
    
    def get_enabled_services(self, category: str = None) -> List[Service]:
        query = self.db.query(Service).filter(
            Service.guild_id == self.guild_id,
            Service.enabled == True
        )
        if category:
            query = query.filter(Service.category == category.lower())
        return query.order_by(Service.category, Service.name).all()
    
    def get_service_by_name(self, name: str) -> Optional[Service]:
        return self.db.query(Service).filter(
            Service.guild_id == self.guild_id,
            Service.name == name.lower()
        ).first()
    
    def validate_generator_access(self, tier: str, member: discord.Member) -> Tuple[bool, str]:
        if tier == "free":
            return self.get_setting("free_gen_enabled", True), ""
        
        enabled_key = f"{tier}_gen_enabled"
        role_key = f"{tier}_gen_role_id"
        
        if not self.get_setting(enabled_key, False):
            return False, f"{GENERATOR_TIER_DISPLAY.get(tier, tier)} generator is disabled"
        
        role_id = self.get_setting(role_key)
        if role_id:
            role = member.guild.get_role(role_id)
            if not role or role not in member.roles:
                return False, f"You need the {role.name if role else 'required'} role to use {GENERATOR_TIER_DISPLAY.get(tier, tier)} generator"
        
        return True, ""
    
    def get_generator_cooldown(self, tier: str) -> int:
        return self.get_setting(f"{tier}_gen_cooldown", DEFAULT_SETTINGS.get(f"{tier}_gen_cooldown", 60))
    
    def get_generator_code_length(self, tier: str) -> int:
        return self.get_setting(f"{tier}_gen_code_length", DEFAULT_SETTINGS.get(f"{tier}_gen_code_length", 5))
    
    def get_generator_category(self, tier: str) -> str:
        return self.get_setting(f"{tier}_gen_category", tier)
    
    def get_generator_services(self, tier: str) -> List[str]:
        return self.get_setting(f"{tier}_gen_services", [])
    
    def get_success_message(self, tier: str) -> str:
        return self.get_setting(f"{tier}_gen_success_message", DEFAULT_SETTINGS.get(f"{tier}_gen_success_message", ""))
    
    def get_dm_guidance(self, tier: str) -> str:
        return self.get_setting(f"{tier}_gen_dm_guidance", DEFAULT_SETTINGS.get(f"{tier}_gen_dm_guidance", ""))
    
    def get_ads_url(self) -> str:
        from config import ADS_WEBSITE_URL
        return self.get_setting("ads_website_url", ADS_WEBSITE_URL) or ""
    
    def get_form_url(self) -> str:
        from config import GOOGLE_FORM_URL
        return GOOGLE_FORM_URL or ""
    
    def get_ticket_panel_channel_id(self) -> Optional[int]:
        return self.get_setting("ticket_panel_channel_id")
    
    def get_log_channel_id(self) -> Optional[int]:
        return self.get_setting("ticket_log_channel_id")
    
    def get_staff_role_id(self) -> Optional[int]:
        return self.get_setting("ticket_staff_role_id")
    
    def log_config_change(self, admin_id: int, setting: str, option: str, old_value: Any, new_value: Any):
        log = Log(
            guild_id=self.guild_id,
            action="config_changed",
            discord_id=admin_id,
            details=f"Setting: {setting}\nOption: {option}\nOld: {old_value}\nNew: {new_value}"
        )
        self.db.add(log)
        self.db.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        total_users = self.db.query(User).filter(User.guild_id == self.guild_id).count()
        verified_users = self.db.query(User).filter(
            User.guild_id == self.guild_id,
            User.verified == True
        ).count()
        
        total_codes = self.db.query(Code).filter(Code.guild_id == self.guild_id).count()
        unused_codes = self.db.query(Code).filter(
            Code.guild_id == self.guild_id,
            Code.status == "unused"
        ).count()
        redeemed_codes = self.db.query(Code).filter(
            Code.guild_id == self.guild_id,
            Code.status == "redeemed"
        ).count()
        expired_codes = self.db.query(Code).filter(
            Code.guild_id == self.guild_id,
            Code.status == "expired"
        ).count()
        
        active_tickets = self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.status == "open"
        ).count()
        closed_tickets = self.db.query(Ticket).filter(
            Ticket.guild_id == self.guild_id,
            Ticket.status == "closed"
        ).count()
        
        services = self.db.query(Service).filter(Service.guild_id == self.guild_id).all()
        service_stats = {}
        for service in services:
            count = self.db.query(Code).filter(
                Code.guild_id == self.guild_id,
                Code.service_id == service.id
            ).count()
            service_stats[service.name] = count
        
        return {
            "users": {"total": total_users, "verified": verified_users},
            "codes": {"total": total_codes, "unused": unused_codes, "redeemed": redeemed_codes, "expired": expired_codes},
            "tickets": {"active": active_tickets, "closed": closed_tickets},
            "services": service_stats
        }

import discord


def get_setting(guild_id: int, key: str, default: Any = None) -> Any:
    from database import get_db
    db = next(get_db())
    try:
        service = ConfigurationService(db, guild_id)
        return service.get_setting(key, default)
    finally:
        db.close()


def set_setting(guild_id: int, key: str, value: Any, updated_by: int = None) -> Any:
    from database import get_db
    db = next(get_db())
    try:
        service = ConfigurationService(db, guild_id)
        return service.set_setting(key, value, updated_by)
    finally:
        db.close()


def is_enabled(guild_id: int, key: str, default: bool = False) -> bool:
    value = get_setting(guild_id, key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)


def get_int_setting(guild_id: int, key: str, default: int = 0) -> int:
    value = get_setting(guild_id, key, default)
    try:
        return int(value)
    except (ValueError, TypeError):
        return default