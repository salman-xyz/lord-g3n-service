import discord
from typing import List
from config import GENERATOR_TIERS, GENERATOR_TIER_DISPLAY
from database import Service

class GeneratorTierSelect(discord.ui.Select):
    def __init__(self, config_service, services_by_tier: dict):
        options = []
        for tier in GENERATOR_TIERS:
            if config_service.get_setting(f"{tier}_gen_enabled", False):
                services = services_by_tier.get(tier, [])
                if services:
                    options.append(discord.SelectOption(
                        label=GENERATOR_TIER_DISPLAY.get(tier, tier),
                        description=f"{len(services)} services available",
                        value=tier
                    ))
        
        if not options:
            options.append(discord.SelectOption(
                label="No generators available",
                description="No generators are currently enabled",
                value="none"
            ))
        
        super().__init__(
            placeholder="Select generator tier...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="generator_tier_select"
        )
        self.config_service = config_service
        self.services_by_tier = services_by_tier
    
    async def callback(self, interaction: discord.Interaction):
        tier = self.values[0]
        if tier == "none":
            await interaction.response.send_message("❌ No generators are currently available.", ephemeral=True)
            return
        
        services = self.services_by_tier.get(tier, [])
        if not services:
            await interaction.response.send_message(f"❌ No services available for {GENERATOR_TIER_DISPLAY.get(tier, tier)}.", ephemeral=True)
            return
        
        from views.generator_views import ServiceSelectView
        view = ServiceSelectView(self.config_service, tier, services)
        embed = discord.Embed(
            title=f"{GENERATOR_TIER_DISPLAY.get(tier, tier)} Generator",
            description="Select a service to generate:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

class GeneratorView(discord.ui.View):
    def __init__(self, config_service, services_by_tier: dict):
        super().__init__(timeout=60)
        self.add_item(GeneratorTierSelect(config_service, services_by_tier))

class ServiceSelect(discord.ui.Select):
    def __init__(self, config_service, tier: str, services: List[Service]):
        options = []
        for service in services[:25]:
            options.append(discord.SelectOption(
                label=service.name.capitalize(),
                description=f"Category: {service.category}",
                value=service.name
            ))
        
        super().__init__(
            placeholder="Select a service...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="service_select"
        )
        self.config_service = config_service
        self.tier = tier
        self.services = {s.name: s for s in services}
    
    async def callback(self, interaction: discord.Interaction):
        service_name = self.values[0]
        service = self.services.get(service_name)
        
        if not service:
            await interaction.response.send_message("❌ Service not found.", ephemeral=True)
            return
        
        can_access, msg = self.config_service.validate_generator_access(self.tier, interaction.user)
        if not can_access:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
            return
        
        from services.code_generator import CodeGenerator
        db = next(__import__('database').get_db())
        code_gen = CodeGenerator(db, interaction.guild.id)
        
        user_codes = code_gen.get_user_codes(interaction.user.id, "unused")
        tier_services = self.config_service.get_generator_services(self.tier)
        
        if service_name not in tier_services:
            await interaction.response.send_message("❌ This service is not available in this generator tier.", ephemeral=True)
            return
        
        if user_codes:
            has_same_service = any(c.service_id == service.id for c in user_codes)
            if has_same_service:
                await interaction.response.send_message("❌ You already have an unused code for this service. Please redeem it first.", ephemeral=True)
                return
        
        cooldown = self.config_service.get_generator_cooldown(self.tier)
        if cooldown > 0:
            from datetime import datetime, timedelta
            recent_codes = db.query(__import__('database').Code).filter(
                __import__('database').Code.guild_id == interaction.guild.id,
                __import__('database').Code.discord_id == interaction.user.id,
                __import__('database').Code.created_at >= datetime.utcnow() - timedelta(seconds=cooldown)
            ).all()
            if recent_codes:
                remaining = cooldown - int((datetime.utcnow() - recent_codes[0].created_at).total_seconds())
                await interaction.response.send_message(f"⏳ Cooldown active. Please wait {remaining} seconds.", ephemeral=True)
                return
        
        await interaction.response.defer()
        
        code_str = await code_gen.generate_unique_code()
        if not code_str:
            await interaction.followup.send("❌ Failed to generate unique code. Please try again.", ephemeral=True)
            return
        
        new_code = code_gen.create_code(
            interaction.user.id,
            service,
            self.config_service.get_generator_category(self.tier),
            self.tier,
            code_str
        )
        
        from services.logging_service import LoggingService
        log_service = LoggingService(db, interaction.guild.id)
        log_service.log_code_generated(interaction.user.id, code_str, service.name, self.config_service.get_generator_category(self.tier))
        
        category = self.config_service.get_generator_category(self.tier)
        embed = build_success_embed(category, service.name, self.config_service, interaction.user)
        await interaction.followup.send(embed=embed)
        
        form_url = self.config_service.get_ads_url() or self.config_service.get_form_url()
        ticket_ch_id = self.config_service.get_ticket_panel_channel_id()
        guild_id = interaction.guild.id if interaction.guild else None
        
        dm_embed = build_dm_embed(code_str, form_url, ticket_ch_id, guild_id)
        
        try:
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            await interaction.followup.send("⚠️ Your account was generated successfully, but I couldn't send you a DM. Please enable your Discord DMs and contact staff.", ephemeral=True)

class ServiceSelectView(discord.ui.View):
    def __init__(self, config_service, tier: str, services: List[Service]):
        super().__init__(timeout=60)
        self.add_item(ServiceSelect(config_service, tier, services))
        
        back_button = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, emoji="↩️", row=1)
        back_button.callback = self.go_back
        self.add_item(back_button)
    
    async def go_back(self, interaction: discord.Interaction):
        from views.generator_views import GeneratorView
        services_by_tier = {}
        for tier in GENERATOR_TIERS:
            services = self.config_service.get_enabled_services(tier)
            if services:
                services_by_tier[tier] = services
        view = GeneratorView(self.config_service, services_by_tier)
        embed = discord.Embed(
            title="🎫 LORD G3N SERVICES - Generator",
            description="Select a generator tier to begin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

def build_success_embed(category: str, service_name: str, config_service=None, user=None) -> discord.Embed:
    title = f"🎉 {category.capitalize()} Account Generated"
    user_mention = f"<@{user.id}>" if user else "You"
    desc = f"{user_mention} Your `{service_name}` account is successfully Generated!\nCheck your DM!"
    
    embed = discord.Embed(
        title=title,
        description=desc,
        color=discord.Color.green()
    )
    
    # Add GIF if set
    gif_url = None
    if config_service:
        gif_url = config_service.get_setting("gen_gif_url")
    if gif_url:
        embed.set_image(url=gif_url)
    
    return embed


def build_dm_embed(code: str, form_url: str = None, ticket_ch_id: int = None, guild_id: int = None, title: str = "Lord G3N") -> discord.Embed:
    link_url = form_url if form_url else "https://cuty.io/WmdFdRau7cUQ"
    
    if guild_id and ticket_ch_id:
        ticket_link = f"[Ticket channel](https://discord.com/channels/{guild_id}/{ticket_ch_id})"
    elif ticket_ch_id:
        ticket_link = f"<#{ticket_ch_id}>"
    else:
        ticket_link = "[Ticket channel](https://discord.com/channels/@me)"
        
    desc = (
        "Follow these steps to redeem your code:\n\n"
        f"Step 1: Click on this [LINK]({link_url}), complete some steps, and submit your Discord username in the forms.\n"
        f"Step 2: Go to the {ticket_link}.\n"
        "Step 3: Click on Redeem a code.\n"
        "Step 4: Send this code to staff:\n\n"
        "**Code**\n"
        f"```{code}```"
    )
    
    embed = discord.Embed(
        title=title,
        description=desc,
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    return embed


def build_dm_message(user, code: str, form_url: str, ticket_ch_id: int, guild_id: int = None) -> str:
    ticket_channel = f"<#{ticket_ch_id}>" if ticket_ch_id else "#tickets"
    form_link = f"[LINK]({form_url})" if form_url else "the verification form"
    return (
        f"🎉 **Your account has been successfully generated!**\n\n"
        f"Follow these steps to redeem your code:\n\n"
        f"**Step 1:** Click on this {form_link}, complete some steps, and submit your Discord username in the forms.\n\n"
        f"**Step 2:** Go to the Ticket channel: {ticket_channel}\n\n"
        f"**Step 3:** Click on **Redeem a code**.\n\n"
        f"**Step 4:** Send this code to staff:\n\n"
        f"**Code**\n```{code}```"
    )


def build_custom_success_message(custom_msg: str, user, service_name: str, service_category: str, code: str, form_url: str, ticket_ch_id: int, guild_id: int) -> str:
    return custom_msg.format(
        user=user.name,
        username=user.name,
        user_id=user.id,
        service=service_name,
        category=service_category,
        code=code,
        form_url=form_url,
        ticket_channel=f"<#{ticket_ch_id}>" if ticket_ch_id else "#tickets"
    )


class PersistentGeneratorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)