import time
import discord
from discord.ext import commands

from database import get_session
from database import Service
from services.configuration_service import ConfigurationService, get_setting, is_enabled, get_int_setting
from services.code_generator import create_code
from services.verification_service import get_or_create_user
from services.logging_service import create_log_entry
from views.generator_views import build_success_embed, build_dm_embed, build_dm_message, build_custom_success_message

class GeneratorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cooldowns = {}  # {(guild_id, user_id): last_gen_time}
    
    @commands.command(name='gen')
    async def gen_command(self, ctx, service_name: str = None):
        """Generate an account code. Usage: !gen <service>"""
        if not service_name:
            await ctx.send('❌ Please specify a service. Usage: `!gen <service>`')
            return
        
        guild_id = ctx.guild.id
        user = ctx.author
        service_name = service_name.lower()
        
        # Create config service instance
        with get_session() as session:
            config_service = ConfigurationService(session, guild_id)
            
            # 1. Check service exists
            service = session.query(Service).filter_by(guild_id=guild_id, name=service_name).first()
            if not service:
                await ctx.send(f'❌ Service `{service_name}` not found.')
                return
            if not service.enabled:
                await ctx.send(f'❌ Service `{service_name}` is currently disabled.')
                return
            service_category = service.category
            service_id = service.id
            session.expunge(service)
        
        # 2. Determine generator tier based on category
        gen_type = service_category.lower()  # free, booster, premium, extreme
        
        # 3. Check generator enabled
        if not is_enabled(guild_id, f'{gen_type}_gen_enabled'):
            await ctx.send(f'❌ The {gen_type} generator is currently disabled.')
            return
        
        # 4. Check required role (for non-free tiers)
        if gen_type != 'free':
            required_role_id = get_setting(guild_id, f'{gen_type}_gen_role')
            if required_role_id:
                role = ctx.guild.get_role(int(required_role_id))
                if role and role not in user.roles:
                    await ctx.send(f'❌ You need the {role.mention} role to use the {gen_type} generator.')
                    return
        
        # 5. Check cooldown
        cooldown = get_int_setting(guild_id, f'{gen_type}_gen_cooldown', 60)
        cooldown_key = (guild_id, user.id, gen_type)
        now = time.time()
        if cooldown_key in self._cooldowns:
            elapsed = now - self._cooldowns[cooldown_key]
            if elapsed < cooldown:
                remaining = int(cooldown - elapsed)
                await ctx.send(f'⏱️ You are on cooldown. Please wait {remaining} seconds.')
                return
        
        # 6. Generate code
        code_length = get_int_setting(guild_id, f'{gen_type}_gen_code_length', 5)
        try:
            # Create a minimal service object for code generation
            service_obj = Service(id=service_id, name=service_name, category=service_category, guild_id=guild_id, enabled=True)
            code = create_code(guild_id, user.id, service_obj, service_category, gen_type, code_length)
        except Exception as e:
            await ctx.send(f'❌ Failed to generate code: {e}')
            return
        
        # 7. Set cooldown
        self._cooldowns[cooldown_key] = now
        
        # 8. Ensure user record exists
        get_or_create_user(guild_id, user.id, user.name)
        
        # 9. Send success message
        with get_session() as session:
            config_service = ConfigurationService(session, guild_id)
            
            embed = build_success_embed(service_category, service_name, config_service, user)
            await ctx.send(embed=embed)
            
            # 10. DM the user
            form_url = config_service.get_ads_url() or config_service.get_form_url()
            ticket_ch_id = config_service.get_ticket_panel_channel_id()
            
            dm_embed = build_dm_embed(code.code, form_url, ticket_ch_id, guild_id)
            
            try:
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                await ctx.send("⚠️ Your account was generated successfully, but I couldn't send you a DM.\n\nPlease enable your Discord DMs and contact staff.")
            
            # 11. Log
            create_log_entry(guild_id, 'Code Generated', user.id, details=f'Service: {service_name}, Category: {service_category}, Code: {code.code}')

async def setup(bot):
    await bot.add_cog(GeneratorCog(bot))
