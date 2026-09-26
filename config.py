import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Form Responses 1")
GOOGLE_FORM_URL = os.getenv("GOOGLE_FORM_URL")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")
VERIFICATION_SYNC_INTERVAL = int(os.getenv("VERIFICATION_SYNC_INTERVAL", "30"))

ADS_WEBSITE_URL = os.getenv("ADS_WEBSITE_URL")

TICKET_PANEL_CHANNEL_ID = int(os.getenv("TICKET_PANEL_CHANNEL_ID", "0")) if os.getenv("TICKET_PANEL_CHANNEL_ID") else None
TICKET_LOG_CHANNEL_ID = int(os.getenv("TICKET_LOG_CHANNEL_ID", "0")) if os.getenv("TICKET_LOG_CHANNEL_ID") else None

REDEEM_TICKET_CATEGORY_ID = int(os.getenv("REDEEM_TICKET_CATEGORY_ID", "0")) if os.getenv("REDEEM_TICKET_CATEGORY_ID") else None
REWARD_TICKET_CATEGORY_ID = int(os.getenv("REWARD_TICKET_CATEGORY_ID", "0")) if os.getenv("REWARD_TICKET_CATEGORY_ID") else None
SUPPORT_TICKET_CATEGORY_ID = int(os.getenv("SUPPORT_TICKET_CATEGORY_ID", "0")) if os.getenv("SUPPORT_TICKET_CATEGORY_ID") else None

STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "0")) if os.getenv("STAFF_ROLE_ID") else None

GEN_COOLDOWN = int(os.getenv("GEN_COOLDOWN", "60"))
MAX_ACTIVE_TICKETS = int(os.getenv("MAX_ACTIVE_TICKETS", "1"))

CODE_LENGTH = int(os.getenv("CODE_LENGTH", "5"))

DEFAULT_SETTINGS = {
    "prefix": "!",
    "free_gen_enabled": True,
    "free_gen_cooldown": 60,
    "free_gen_code_length": 5,
    "free_gen_category": "free",
    "free_gen_services": [],
    "free_gen_success_message": "🎉 Account Successfully Generated!\n\nCategory: {category}\nService: {service}\n\nYour redemption code has been generated.\n\n📩 Check your DMs for the redemption instructions.",
    "free_gen_dm_guidance": "🎉 Your account has been successfully generated!\n\nFollow these steps to redeem your code:\n\nStep 1: Click on this [LINK]({form_url}), complete some steps, and submit your Discord username in the forms.\n\nStep 2: Go to the Ticket channel: {ticket_channel}\n\nStep 3: Click on Redeem a code.\n\nStep 4: Send this code to staff:\n\nCode:\n```{code}```",
    "booster_gen_enabled": False,
    "booster_gen_role_id": None,
    "booster_gen_cooldown": 60,
    "booster_gen_code_length": 5,
    "booster_gen_category": "booster",
    "booster_gen_services": [],
    "booster_gen_success_message": "🎉 Account Successfully Generated!\n\nCategory: {category}\nService: {service}\n\nYour redemption code has been generated.\n\n📩 Check your DMs for the redemption instructions.",
    "booster_gen_dm_guidance": "🎉 Your account has been successfully generated!\n\nFollow these steps to redeem your code:\n\nStep 1: Click on this [LINK]({form_url}), complete some steps, and submit your Discord username in the forms.\n\nStep 2: Go to the Ticket channel: {ticket_channel}\n\nStep 3: Click on Redeem a code.\n\nStep 4: Send this code to staff:\n\nCode:\n```{code}```",
    "premium_gen_enabled": False,
    "premium_gen_role_id": None,
    "premium_gen_cooldown": 60,
    "premium_gen_code_length": 5,
    "premium_gen_category": "premium",
    "premium_gen_services": [],
    "premium_gen_success_message": "🎉 Account Successfully Generated!\n\nCategory: {category}\nService: {service}\n\nYour redemption code has been generated.\n\n📩 Check your DMs for the redemption instructions.",
    "premium_gen_dm_guidance": "🎉 Your account has been successfully generated!\n\nFollow these steps to redeem your code:\n\nStep 1: Click on this [LINK]({form_url}), complete some steps, and submit your Discord username in the forms.\n\nStep 2: Go to the Ticket channel: {ticket_channel}\n\nStep 3: Click on Redeem a code.\n\nStep 4: Send this code to staff:\n\nCode:\n```{code}```",
    "extreme_gen_enabled": False,
    "extreme_gen_role_id": None,
    "extreme_gen_cooldown": 60,
    "extreme_gen_code_length": 5,
    "gen_gif_url": None,
    "extreme_gen_category": "extreme",
    "extreme_gen_services": [],
    "extreme_gen_success_message": "🎉 Account Successfully Generated!\n\nCategory: {category}\nService: {service}\n\nYour redemption code has been generated.\n\n📩 Check your DMs for the redemption instructions.",
    "extreme_gen_dm_guidance": "🎉 Your account has been successfully generated!\n\nFollow these steps to redeem your code:\n\nStep 1: Click on this [LINK]({form_url}), complete some steps, and submit your Discord username in the forms.\n\nStep 2: Go to the Ticket channel: {ticket_channel}\n\nStep 3: Click on Redeem a code.\n\nStep 4: Send this code to staff:\n\nCode:\n```{code}```",
    "ticket_staff_role_id": None,
    "ticket_log_channel_id": None,
    "ticket_panel_channel_id": None,
    "ticket_gif_url": None,
    "redeem_ticket_category_id": None,
    "reward_ticket_category_id": None,
    "purchase_ticket_category_id": None,
    "report_ticket_category_id": None,
    "partnership_ticket_category_id": None,
    "support_ticket_category_id": None,
    "max_active_tickets": 1,
    "ticket_name_format": "{type}-{username}",
    "ticket_welcome_message": "Welcome {user_mention},\n\n**Please wait until our support team assists you shortly.**\n\n**Category**\n{category}\n\n**Service**\n{service}\n\nPowered by Lord G3N Services",
    "delete_reason_required": True,
    "auto_delete_delay": 5,
    "add_account_enabled": False,
    "add_account_staff_role_id": None,
    "admin_role_id": None,
    "add_account_format": "{service}:{email}:{password}",
    "add_account_service": "",
    "add_account_category": "",
    "add_account_logging": False,
    "add_account_log_channel_id": None,
    "add_account_delivery_method": "dm",
    "drop_enabled": False,
    "drop_channel_id": None,
    "drop_cooldown": 3600,
    "drop_type": "single",
    "drop_services": [],
    "drop_max_claims": 1,
    "drop_message": "🎁 Drop Started!\n\nService: {service}\nClaims: {max_claims}\n\nClick the button below to claim!",
    "drop_claim_message": "🎉 You claimed a drop!\n\nService: {service}\nCode: `{code}`",
    "drop_auto_close": True,
    "send_account_enabled": False,
    "send_account_staff_role_id": None,
    "send_account_delivery_method": "dm",
    "send_account_confirmation": True,
    "send_account_message": "📦 Account Delivered\n\nService: {service}\nAccount: `{account}`",
    "send_account_logging": False,
    "send_account_log_channel_id": None,
    "vouch_enabled": False,
    "vouch_channel_id": None,
    "vouch_required_role_id": None,
    "vouch_message": "⭐ New Vouch!\n\nUser: {user_mention}\nService: {service}\nFeedback: {feedback}",
    "vouch_logging": False,
    "vouch_log_channel_id": None,
    "vouch_cooldown": 300,
    "cheer_enabled": False,
    "cheer_channel_id": None,
    "cheer_allowed_role_id": None,
    "cheer_cooldown": 60,
    "cheer_message": "🎉 Cheer!\n\n{user_mention} is cheering!",
    "cheer_emoji": "🎉",
    "cheer_logging": False,
    "remove_account_enabled": False,
    "remove_account_staff_role_id": None,
    "remove_account_reason_required": True,
    "remove_account_confirmation": True,
    "remove_account_log_channel_id": None,
    "remove_account_message": "🗑️ Account Removed\n\nService: {service}\nReason: {reason}",
    "remove_account_history_option": "archive",
    "upload_cookie_enabled": False,
    "upload_cookie_staff_role_id": None,
    "upload_cookie_channel_id": None,
    "upload_cookie_file_types": [".json", ".txt"],
    "upload_cookie_max_size": 10485760,
    "upload_cookie_logging": False,
    "upload_cookie_log_channel_id": None,
    "clean_accounts_enabled": False,
    "clean_accounts_schedule": "manual",
    "clean_accounts_target_service": "",
    "clean_accounts_statuses": ["expired", "invalid", "duplicate"],
    "clean_accounts_expired_cleanup": True,
    "clean_accounts_duplicate_cleanup": True,
    "clean_accounts_auto_delete": False,
    "clean_accounts_confirmation": True,
    "clean_accounts_log_channel_id": None,
    "promotion_enabled": False,
    "promotion_channel_id": None,
    "promotion_url": "",
    "promotion_message": "📢 Check out our server!\n\n{server}\n{invite}\n{website}",
    "promotion_cooldown": 3600,
    "promotion_required_role_id": None,
    "promotion_image_url": "",
    "promotion_auto": False,
    "bulk_vouch_enabled": False,
    "bulk_vouch_staff_role_id": None,
    "bulk_vouch_max_operations": 10,
    "bulk_vouch_channel_id": None,
    "bulk_vouch_confirmation": True,
    "bulk_vouch_logging": False,
    "bulk_vouch_log_channel_id": None,
    "automod_enabled": False,
    "automod_anti_spam": False,
    "automod_spam_limit": 5,
    "automod_spam_window": 10,
    "automod_anti_link": False,
    "automod_allowed_domains": [],
    "automod_mention_spam": False,
    "automod_max_mentions": 5,
    "automod_duplicate_detection": False,
    "automod_bad_word_filter": False,
    "automod_filter_words": [],
    "automod_punishment": "delete",
    "automod_timeout_duration": 300,
    "automod_warning_limit": 3,
    "automod_log_channel_id": None,
}

GENERATOR_TIERS = ["free", "booster", "premium", "extreme"]
GENERATOR_TIER_DISPLAY = {
    "free": "🆓 Free",
    "booster": "🚀 Booster",
    "premium": "💎 Premium",
    "extreme": "⚡ Extreme",
}

TICKET_TYPES = {
    "redeem": {"emoji": "🎟️", "label": "Redeem a Code", "description": "Use a generated service code"},
    "reward": {"emoji": "🎁", "label": "Reward", "description": "Open a Ticket to claim Rewards"},
    "purchase": {"emoji": "🛒", "label": "Purchase", "description": "Buy products/services"},
    "report": {"emoji": "⚠️", "label": "Report", "description": "Report issues or users"},
    "partnership": {"emoji": "🤝", "label": "Partnership", "description": "Open a Ticket for Partnership with us"},
    "support": {"emoji": "🛠️", "label": "Support", "description": "General support and help"},
}

CODE_STATUSES = ["unused", "activated", "redeemed", "expired", "invalidated"]

PANEL_CATEGORIES = [
    ("prefix", "🔤 Prefix Settings", "Change command prefix"),
    ("free_gen", "🆓 Free Gen Settings", "Configure Free Generator"),
    ("booster_gen", "🚀 Booster Gen Settings", "Configure Booster Generator"),
    ("premium_gen", "💎 Premium Gen Settings", "Configure Premium Generator"),
    ("extreme_gen", "⚡ Extreme Gen Settings", "Configure Extreme Generator"),
    ("ticket", "🎟️ Ticket Settings", "Configure ticket system"),
    ("add_account", "➕ Add Account Settings", "Configure add account"),
    ("drop", "🎁 Drop Settings", "Configure drops"),
    ("send_account", "📤 Send Account Settings", "Configure send account"),
    ("vouch", "👍 Vouch Settings", "Configure vouch system"),
    ("cheer", "🎉 Cheer Settings", "Configure cheer system"),
    ("remove_account", "🗑️ Remove Account Settings", "Configure remove account"),
    ("upload_cookie", "🍪 Upload Cookie Settings", "Configure cookie upload"),
    ("clean_accounts", "🧹 Clean Accounts Settings", "Configure account cleaning"),
    ("promotion", "📈 Promotion Settings", "Configure promotions"),
    ("bulk_vouch", "📝 Bulk Vouch Settings", "Configure bulk vouch"),
    ("automod", "🤖 AutoMod Settings", "Configure AutoMod"),
]