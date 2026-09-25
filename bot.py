import os
import sys
import logging
import asyncio
import discord
from discord.ext import commands, tasks
import config as Config
from database import init_db
from services.configuration_service import get_setting

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('LordG3N')

# Dynamic prefix
def get_prefix(bot, message):
    if not message.guild:
        return getattr(Config, 'BOT_PREFIX', '!')
    prefix = get_setting(message.guild.id, 'prefix', getattr(Config, 'BOT_PREFIX', '!'))
    return commands.when_mentioned_or(prefix)(bot, message)

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# Extensions to load
EXTENSIONS = [
    'commands.generator',
    'commands.verification',
    'commands.tickets',
    'commands.services',
    'commands.admin',
    'commands.panel',
]

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guild(s)')
    
    # Restore ticket views for open tickets
    await restore_ticket_views()
    
    # Start Google Sheets polling
    if not google_sheets_sync.is_running():
        google_sheets_sync.start()

async def restore_ticket_views():
    """Restore button views for all open tickets after bot restart"""
    from database import get_db, Ticket
    from services.ticket_service import TicketService
    from views.ticket_buttons import TicketButtonsView
    
    db = next(get_db())
    try:
        for guild in bot.guilds:
            tickets = db.query(Ticket).filter(
                Ticket.guild_id == guild.id,
                Ticket.status == "open"
            ).all()
            
            for ticket in tickets:
                channel = guild.get_channel(ticket.channel_id)
                if not channel:
                    logger.warning(f"Ticket {ticket.id}: Channel {ticket.channel_id} not found (may have been deleted)")
                    # Optionally auto-close stale tickets
                    continue
                
                ticket_service = TicketService(db, guild.id)
                staff_role_id = ticket_service.get_staff_role_id()
                
                view = TicketButtonsView(ticket_service, ticket, staff_role_id)
                # Views with dynamic custom_ids (per-ticket) can't be pre-registered globally
                # They need to be attached to messages. For now, log that manual intervention may be needed.
                logger.info(f"Ticket {ticket.id} in #{channel.name} needs view re-attachment (run !ticketpanels to refresh panel)")
    except Exception as e:
        logger.error(f"Failed to restore ticket views: {e}")
    finally:
        db.close()

async def setup_hook():
    # Register persistent views
    try:
        from views.ticket_panel import PersistentTicketPanelView
        from views.ticket_buttons import PersistentTicketButtonsView
        
        bot.add_view(PersistentTicketPanelView())
        bot.add_view(PersistentTicketButtonsView())
    except ImportError as e:
        logger.warning(f"Could not load views: {e}")
    
    # Load extensions
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            logger.info(f'Loaded extension: {ext}')
        except Exception as e:
            logger.error(f'Failed to load extension {ext}: {e}')

bot.setup_hook = setup_hook

# Google Sheets polling task
@tasks.loop(seconds=getattr(Config, 'VERIFICATION_SYNC_INTERVAL', 60))
async def google_sheets_sync():
    from services.google_sheets import process_sheet_for_guild
    for guild in bot.guilds:
        try:
            stats = await process_sheet_for_guild(guild.id, guild)
            if stats.get('new_submissions', 0) > 0:
                logger.info(f'Google Sheets sync for {guild.name}: {stats}')
        except Exception as e:
            logger.error(f'Google Sheets sync error for {guild.name}: {e}')

@google_sheets_sync.before_loop
async def before_sync():
    await bot.wait_until_ready()

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ You do not have permission to use this command.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'❌ Missing required argument: `{error.param.name}`')
    elif isinstance(error, commands.CommandNotFound):
        pass  # Silently ignore
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f'❌ Invalid argument: {error}')
    else:
        logger.error(f'Command error in {ctx.command}: {error}', exc_info=error)
        await ctx.send('❌ An unexpected error occurred.')

# Run
def main():
    if not getattr(Config, 'DISCORD_TOKEN', None):
        logger.error('DISCORD_TOKEN not set in config!')
        sys.exit(1)
    
    init_db()
    logger.info('Database initialized.')
    
    bot.run(Config.DISCORD_TOKEN, log_level=logging.INFO)

if __name__ == '__main__':
    main()
