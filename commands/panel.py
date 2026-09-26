import time
import re
import datetime
import discord
from urllib.parse import urlparse
from discord.ext import commands

from database import get_db
from views.config_panel import ConfigPanelView, build_main_panel_embed
from services.configuration_service import ConfigurationService
from services.ticket_service import TicketService
from services.verification_service import VerificationService
from services.configuration_service import get_setting, is_enabled, get_int_setting
from commands.admin import is_admin_or_has_role

class PanelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._spam_tracker = {}  # {(guild_id, user_id): [timestamps]}
        self._message_cache = {}  # {(guild_id, user_id): [messages]}
    
    @commands.command(name='panel')
    @is_admin_or_has_role()
    async def panel_command(self, ctx):
        embed = build_main_panel_embed(ctx.guild.id)
        db = next(get_db())
        try:
            config_service = ConfigurationService(db, ctx.guild.id)
            ticket_service = TicketService(db, ctx.guild.id)
            verification_service = VerificationService(db, ctx.guild.id)
            view = ConfigPanelView(config_service, ctx.guild.id)
            await ctx.send(embed=embed, view=view)
        finally:
            db.close()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        guild_id = message.guild.id
        if not is_enabled(guild_id, 'automod_enabled'):
            return
        
        # Anti-spam
        if is_enabled(guild_id, 'automod_anti_spam'):
            # Track messages per user
            key = (guild_id, message.author.id)
            now = time.time()
            window = get_int_setting(guild_id, 'automod_spam_window', 5)
            limit = get_int_setting(guild_id, 'automod_spam_limit', 5)
            
            if key not in self._spam_tracker:
                self._spam_tracker[key] = []
            self._spam_tracker[key] = [t for t in self._spam_tracker[key] if now - t < window]
            self._spam_tracker[key].append(now)
            
            if len(self._spam_tracker[key]) > limit:
                await self._punish(message, 'Spam detected')
                return
        
        # Anti-link
        if is_enabled(guild_id, 'automod_anti_link'):
            url_pattern = re.compile(r'https?://\\S+')
            if url_pattern.search(message.content):
                allowed = get_setting(guild_id, 'automod_allowed_domains')
                allowed_list = [d.strip().lower() for d in allowed.split(',') if d.strip()] if allowed else []
                urls = url_pattern.findall(message.content)
                for url in urls:
                    domain = urlparse(url).netloc.lower()
                    if domain and not any(a in domain for a in allowed_list):
                        await self._punish(message, 'Link not allowed')
                        return
        
        # Mention spam
        if is_enabled(guild_id, 'automod_mention_spam'):
            max_mentions = get_int_setting(guild_id, 'automod_max_mentions', 5)
            if len(message.mentions) > max_mentions:
                await self._punish(message, 'Mention spam')
                return
        
        # Duplicate message detection
        if is_enabled(guild_id, 'automod_duplicate_detection'):
            key = (guild_id, message.author.id)
            if key not in self._message_cache:
                self._message_cache[key] = []
            self._message_cache[key].append(message.content)
            if len(self._message_cache[key]) > 10:
                self._message_cache[key] = self._message_cache[key][-10:]
            if self._message_cache[key].count(message.content) >= 3:
                await self._punish(message, 'Duplicate message')
                return
        
        # Bad word filter
        if is_enabled(guild_id, 'automod_bad_word_filter'):
            words = get_setting(guild_id, 'automod_filter_words')
            if words:
                word_list = [w.strip().lower() for w in words.split(',') if w.strip()]
                content_lower = message.content.lower()
                for word in word_list:
                    if word in content_lower:
                        await self._punish(message, f'Filtered word: {word}')
                        return
    
    async def _punish(self, message, reason):
        guild_id = message.guild.id
        punishment = get_setting(guild_id, 'automod_punishment', 'delete')
        
        try:
            if punishment == 'delete':
                await message.delete()
            elif punishment == 'warn':
                await message.delete()
                await message.channel.send(f'⚠️ {message.author.mention}, your message was removed: {reason}', delete_after=10)
            elif punishment == 'timeout':
                await message.delete()
                duration = get_int_setting(guild_id, 'automod_timeout_duration', 60)
                await message.author.timeout(datetime.timedelta(seconds=duration), reason=reason)
            elif punishment == 'kick':
                await message.delete()
                if message.guild.me.guild_permissions.kick_members:
                    await message.author.kick(reason=reason)
            elif punishment == 'ban':
                await message.delete()
                if message.guild.me.guild_permissions.ban_members:
                    await message.author.ban(reason=reason)
        except discord.Forbidden:
            pass
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(PanelCog(bot))
