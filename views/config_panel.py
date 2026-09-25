import discord
from typing import Optional
from config import PANEL_CATEGORIES, GENERATOR_TIERS, GENERATOR_TIER_DISPLAY, DEFAULT_SETTINGS


class SetStaffRoleButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Set Staff Role", style=discord.ButtonStyle.primary, emoji="👮", row=0)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetRoleModal(self.config_service, "ticket_staff_role_id", "Staff Role")
        await interaction.response.send_modal(modal)


class SetLogChannelButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Set Log Channel", style=discord.ButtonStyle.primary, emoji="📋", row=0)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetChannelModal(self.config_service, "ticket_log_channel_id", "Log Channel")
        await interaction.response.send_modal(modal)


class SetPanelChannelButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Set Panel Channel", style=discord.ButtonStyle.primary, emoji="📍", row=1)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetChannelModal(self.config_service, "ticket_panel_channel_id", "Panel Channel")
        await interaction.response.send_modal(modal)


class SetRedeemCategoryButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Redeem Category", style=discord.ButtonStyle.primary, emoji="🎟️", row=1)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetChannelModal(self.config_service, "redeem_ticket_category_id", "Redeem Category")
        await interaction.response.send_modal(modal)


class SetRewardCategoryButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Rewards Category", style=discord.ButtonStyle.primary, emoji="🎁", row=2)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetChannelModal(self.config_service, "rewards_ticket_category_id", "Rewards Category")
        await interaction.response.send_modal(modal)


class SetSupportCategoryButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Support Category", style=discord.ButtonStyle.primary, emoji="🛠️", row=2)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetChannelModal(self.config_service, "support_ticket_category_id", "Support Category")
        await interaction.response.send_modal(modal)


class SetPurchaseCategoryButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Purchase Category", style=discord.ButtonStyle.primary, emoji="🛒", row=3)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetChannelModal(self.config_service, "purchase_ticket_category_id", "Purchase Category")
        await interaction.response.send_modal(modal)


class SetReportCategoryButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Report Category", style=discord.ButtonStyle.primary, emoji="⚠️", row=3)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetChannelModal(self.config_service, "report_ticket_category_id", "Report Category")
        await interaction.response.send_modal(modal)


class SetPartnershipCategoryButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Partnership Category", style=discord.ButtonStyle.primary, emoji="🤝", row=3)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetChannelModal(self.config_service, "partnership_ticket_category_id", "Partnership Category")
        await interaction.response.send_modal(modal)


class SetMaxTicketsButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Max Tickets", style=discord.ButtonStyle.primary, emoji="🔢", row=3)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetIntModal(self.config_service, "max_active_tickets", "Max Active Tickets")
        await interaction.response.send_modal(modal)


class SetNameFormatButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Name Format", style=discord.ButtonStyle.primary, emoji="📝", row=3)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetTextModal(self.config_service, "ticket_name_format", "Ticket Name Format")
        await interaction.response.send_modal(modal)


class SetWelcomeMessageButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Welcome Message", style=discord.ButtonStyle.primary, emoji="👋", row=4)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetLongTextModal(self.config_service, "ticket_welcome_message", "Welcome Message")
        await interaction.response.send_modal(modal)


class SetTicketGifButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Set Panel GIF", style=discord.ButtonStyle.primary, emoji="🖼️", row=4)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetTextModal(self.config_service, "ticket_gif_url", "Ticket Panel GIF URL")
        await interaction.response.send_modal(modal)


class SetGenGifButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Set Gen GIF", style=discord.ButtonStyle.primary, emoji="🎞️", row=4)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetTextModal(self.config_service, "gen_gif_url", "Generator GIF URL")
        await interaction.response.send_modal(modal)


class ToggleDeleteReasonButton(discord.ui.Button):
    def __init__(self, config_service):
        current = config_service.get_setting("delete_reason_required", True)
        label = "Disable Delete Reason" if current else "Enable Delete Reason"
        super().__init__(label=label, style=discord.ButtonStyle.danger if current else discord.ButtonStyle.success, emoji="⚠️", row=4)
        self.config_service = config_service
        self.current = current
    
    async def callback(self, interaction: discord.Interaction):
        new_value = not self.current
        self.config_service.set_setting("delete_reason_required", new_value, interaction.user.id)
        await interaction.response.send_message(f"✅ Delete reason {'enabled' if new_value else 'disabled'}", ephemeral=True)


class SetAutoDeleteDelayButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Auto Delete Delay", style=discord.ButtonStyle.primary, emoji="⏱️", row=4)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetIntModal(self.config_service, "auto_delete_delay", "Auto Delete Delay (seconds)")
        await interaction.response.send_modal(modal)


class CategorySelect(discord.ui.Select):
    def __init__(self, config_service, guild_id: int):
        options = []
        for key, label, description in PANEL_CATEGORIES:
            options.append(discord.SelectOption(
                label=label,
                description=description,
                value=key
            ))
        
        super().__init__(
            placeholder="Select a configuration category...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="config_category_select"
        )
        self.config_service = config_service
        self.guild_id = guild_id
    
    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        await self.show_category_settings(interaction, category)
    
    async def show_category_settings(self, interaction: discord.Interaction, category: str):
        settings = self.get_category_settings(category)
        
        embed = discord.Embed(
            title=f"⚙️ Configuration: {self.get_category_label(category)}",
            description=f"Current settings for **{self.get_category_label(category)}**",
            color=discord.Color.blue()
        )
        
        for key, value in settings.items():
            display_value = self.format_value(key, value)
            embed.add_field(name=key, value=f"`{display_value}`", inline=False)
        
        view = ConfigPanelView(self.config_service, self.guild_id, category)
        await interaction.response.edit_message(embed=embed, view=view)
    
    def get_category_settings(self, category: str) -> dict:
        if category == "prefix":
            return {"prefix": self.config_service.get_setting("prefix", "!")}
        elif category.endswith("_gen") and category.replace("_gen", "") in GENERATOR_TIERS:
            tier = category.replace("_gen", "")
            return self.config_service.get_generator_settings(tier)
        elif category == "ticket":
            return self.config_service.get_ticket_settings()
        elif category in ["add_account", "drop", "send_account", "vouch", "cheer", "remove_account", "upload_cookie", "clean_accounts", "promotion", "bulk_vouch", "automod"]:
            prefix = category + "_"
            settings = {}
            for key, default in DEFAULT_SETTINGS.items():
                if key.startswith(prefix):
                    settings[key] = self.config_service.get_setting(key, default)
            return settings
        return {}
    
    def get_category_label(self, category: str) -> str:
        for key, label, _ in PANEL_CATEGORIES:
            if key == category:
                return label
        return category.capitalize()
    
    def format_value(self, key: str, value: any) -> str:
        if isinstance(value, bool):
            return "Enabled" if value else "Disabled"
        elif isinstance(value, list):
            return ", ".join(str(v) for v in value) if value else "None"
        elif value is None or value == "":
            return "Not set"
        return str(value)


class ConfigPanelView(discord.ui.View):
    def __init__(self, config_service, guild_id: int, current_category: str = None):
        super().__init__(timeout=300)
        self.config_service = config_service
        self.guild_id = guild_id
        self.current_category = current_category
        
        if current_category:
            self.add_item(BackButton())
            self.add_category_settings(current_category)
        else:
            self.add_item(CategorySelect(config_service, guild_id))
    
    def add_category_settings(self, category: str):
        if category == "prefix":
            self.add_item(PrefixModalButton(self.config_service))
        elif category.endswith("_gen") and category.replace("_gen", "") in GENERATOR_TIERS:
            tier = category.replace("_gen", "")
            self.add_generator_settings(tier)
        elif category == "ticket":
            self.add_ticket_settings()
        elif category in ["add_account", "drop", "send_account", "vouch", "cheer", "remove_account", "upload_cookie", "clean_accounts", "promotion", "bulk_vouch", "automod"]:
            self.add_generic_settings(category)
    
    def add_generator_settings(self, tier: str):
        enabled = self.config_service.get_setting(f"{tier}_gen_enabled", False)
        self.add_item(ToggleGeneratorButton(self.config_service, tier, enabled))
        
        if tier != "free":
            self.add_item(SetRoleButton(self.config_service, tier))
        self.add_item(SetCooldownButton(self.config_service, tier))
        self.add_item(SetCodeLengthButton(self.config_service, tier))
        self.add_item(SetServicesButton(self.config_service, tier))
        self.add_item(SetSuccessMessageButton(self.config_service, tier))
        self.add_item(SetDMMessageButton(self.config_service, tier))
        self.add_item(SetGenGifButton(self.config_service))
    
    def add_ticket_settings(self):
        self.add_item(SetStaffRoleButton(self.config_service))
        self.add_item(SetLogChannelButton(self.config_service))
        self.add_item(SetPanelChannelButton(self.config_service))
        self.add_item(SetTicketGifButton(self.config_service))
        self.add_item(SetRedeemCategoryButton(self.config_service))
        self.add_item(SetRewardCategoryButton(self.config_service))
        self.add_item(SetPurchaseCategoryButton(self.config_service))
        self.add_item(SetReportCategoryButton(self.config_service))
        self.add_item(SetPartnershipCategoryButton(self.config_service))
        self.add_item(SetSupportCategoryButton(self.config_service))
        self.add_item(SetMaxTicketsButton(self.config_service))
        self.add_item(SetNameFormatButton(self.config_service))
        self.add_item(SetWelcomeMessageButton(self.config_service))
        self.add_item(ToggleDeleteReasonButton(self.config_service))
        self.add_item(SetAutoDeleteDelayButton(self.config_service))
    
    def add_generic_settings(self, category: str):
        prefix = category + "_"
        enabled_key = f"{prefix}enabled"
        enabled = self.config_service.get_setting(enabled_key, False)
        self.add_item(ToggleFeatureButton(self.config_service, category, enabled_key, enabled))
        
        settings = {}
        for key, default in DEFAULT_SETTINGS.items():
            if key.startswith(prefix) and key != enabled_key:
                settings[key] = self.config_service.get_setting(key, default)
        
        for key, value in settings.items():
            if isinstance(value, bool):
                self.add_item(ToggleSettingButton(self.config_service, key, value))
            elif isinstance(value, int):
                self.add_item(SetIntSettingButton(self.config_service, key, value))
            elif isinstance(value, list):
                self.add_item(SetListSettingButton(self.config_service, key, value))
            elif isinstance(value, str) and len(value) > 100:
                self.add_item(SetLongTextButton(self.config_service, key, value))
            else:
                self.add_item(SetTextSettingButton(self.config_service, key, value))


class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Back to Categories", style=discord.ButtonStyle.secondary, emoji="↩️", row=4)
    
    async def callback(self, interaction: discord.Interaction):
        from views.config_panel import ConfigPanelView
        view = ConfigPanelView(self.view.config_service, self.view.guild_id)
        embed = build_main_panel_embed(self.view.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)


class PrefixModalButton(discord.ui.Button):
    def __init__(self, config_service):
        super().__init__(label="Change Prefix", style=discord.ButtonStyle.primary, emoji="🔤", row=0)
        self.config_service = config_service
    
    async def callback(self, interaction: discord.Interaction):
        modal = PrefixModal(self.config_service)
        await interaction.response.send_modal(modal)


class PrefixModal(discord.ui.Modal):
    def __init__(self, config_service):
        super().__init__(title="Change Command Prefix", timeout=300)
        self.config_service = config_service
        
        self.prefix_input = discord.ui.TextInput(
            label="New Prefix",
            placeholder="Enter new command prefix (e.g., !, ?, /)",
            style=discord.TextStyle.short,
            required=True,
            max_length=5,
            default=config_service.get_setting("prefix", "!")
        )
        self.add_item(self.prefix_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        new_prefix = self.prefix_input.value.strip()
        if not new_prefix:
            await interaction.response.send_message("❌ Prefix cannot be empty.", ephemeral=True)
            return
        
        self.config_service.set_setting("prefix", new_prefix, interaction.user.id)
        await interaction.response.send_message(f"✅ Prefix changed to: `{new_prefix}`", ephemeral=True)


def build_main_panel_embed(guild_id: int) -> discord.Embed:
    embed = discord.Embed(
        title="🎛️ Lord G3N Services - Configuration Panel",
        description="Select a category below to configure settings for your server.\n\n**Note:** Changes take effect immediately.",
        color=discord.Color.dark_blue()
    )
    embed.add_field(
        name="📋 Available Categories",
        value="\n".join([f"`{label}` - {desc}" for _, label, desc in PANEL_CATEGORIES]),
        inline=False
    )
    embed.set_footer(text="Lord G3N Services • Use the dropdown below to navigate")
    return embed


class ToggleGeneratorButton(discord.ui.Button):
    def __init__(self, config_service, tier: str, enabled: bool):
        label = f"Disable {tier.capitalize()} Generator" if enabled else f"Enable {tier.capitalize()} Generator"
        style = discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success
        super().__init__(label=label, style=style, emoji="🎫", row=0)
        self.config_service = config_service
        self.tier = tier
        self.enabled = enabled
    
    async def callback(self, interaction: discord.Interaction):
        new_value = not self.enabled
        self.config_service.set_setting(f"{self.tier}_gen_enabled", new_value, interaction.user.id)
        await interaction.response.send_message(f"✅ {self.tier.capitalize()} generator {'enabled' if new_value else 'disabled'}", ephemeral=True)


class SetRoleButton(discord.ui.Button):
    def __init__(self, config_service, tier: str):
        super().__init__(label=f"Set {tier.capitalize()} Role", style=discord.ButtonStyle.primary, emoji="👑", row=1)
        self.config_service = config_service
        self.tier = tier
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetRoleModal(self.config_service, f"{self.tier}_gen_role_id", f"{self.tier.capitalize()} Role")
        await interaction.response.send_modal(modal)


class SetCooldownButton(discord.ui.Button):
    def __init__(self, config_service, tier: str):
        super().__init__(label="Set Cooldown", style=discord.ButtonStyle.primary, emoji="⏱️", row=2)
        self.config_service = config_service
        self.tier = tier
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetIntModal(self.config_service, f"{self.tier}_gen_cooldown", f"{self.tier.capitalize()} Cooldown (seconds)")
        await interaction.response.send_modal(modal)


class SetCodeLengthButton(discord.ui.Button):
    def __init__(self, config_service, tier: str):
        super().__init__(label="Set Code Length", style=discord.ButtonStyle.primary, emoji="🔢", row=2)
        self.config_service = config_service
        self.tier = tier
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetIntModal(self.config_service, f"{self.tier}_gen_code_length", f"{self.tier.capitalize()} Code Length")
        await interaction.response.send_modal(modal)


class SetServicesButton(discord.ui.Button):
    def __init__(self, config_service, tier: str):
        super().__init__(label="Manage Services", style=discord.ButtonStyle.primary, emoji="📋", row=3)
        self.config_service = config_service
        self.tier = tier
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetTextModal(self.config_service, f"{self.tier}_gen_services", f"{self.tier.capitalize()} Services (comma-separated)")
        await interaction.response.send_modal(modal)


class SetSuccessMessageButton(discord.ui.Button):
    def __init__(self, config_service, tier: str):
        super().__init__(label="Success Message", style=discord.ButtonStyle.primary, emoji="✅", row=3)
        self.config_service = config_service
        self.tier = tier
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetLongTextModal(self.config_service, f"{self.tier}_gen_success_message", f"{self.tier.capitalize()} Success Message")
        await interaction.response.send_modal(modal)


class SetDMMessageButton(discord.ui.Button):
    def __init__(self, config_service, tier: str):
        super().__init__(label="DM Message", style=discord.ButtonStyle.primary, emoji="💬", row=4)
        self.config_service = config_service
        self.tier = tier
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetLongTextModal(self.config_service, f"{self.tier}_gen_dm_message", f"{self.tier.capitalize()} DM Message")
        await interaction.response.send_modal(modal)


class ToggleFeatureButton(discord.ui.Button):
    def __init__(self, config_service, category: str, enabled_key: str, enabled: bool):
        label = f"Disable {category.replace('_', ' ').title()}" if enabled else f"Enable {category.replace('_', ' ').title()}"
        style = discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success
        super().__init__(label=label, style=style, emoji="🔧", row=0)
        self.config_service = config_service
        self.enabled_key = enabled_key
        self.enabled = enabled
    
    async def callback(self, interaction: discord.Interaction):
        new_value = not self.enabled
        self.config_service.set_setting(self.enabled_key, new_value, interaction.user.id)
        await interaction.response.send_message(f"✅ Feature {'enabled' if new_value else 'disabled'}", ephemeral=True)


class ToggleSettingButton(discord.ui.Button):
    def __init__(self, config_service, key: str, value: bool):
        label = f"Disable {key}" if value else f"Enable {key}"
        style = discord.ButtonStyle.danger if value else discord.ButtonStyle.success
        super().__init__(label=label, style=style, emoji="🔘", row=1)
        self.config_service = config_service
        self.key = key
        self.value = value
    
    async def callback(self, interaction: discord.Interaction):
        new_value = not self.value
        self.config_service.set_setting(self.key, new_value, interaction.user.id)
        await interaction.response.send_message(f"✅ Setting updated", ephemeral=True)


class SetIntModal(discord.ui.Modal):
    def __init__(self, config_service, key: str, title: str):
        super().__init__(title=title, timeout=300)
        self.config_service = config_service
        self.key = key
        
        current = config_service.get_setting(key, 0)
        self.value_input = discord.ui.TextInput(
            label="Value",
            placeholder=f"Enter integer value (current: {current})",
            style=discord.TextStyle.short,
            required=True,
            max_length=10,
            default=str(current)
        )
        self.add_item(self.value_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = int(self.value_input.value.strip())
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid integer.", ephemeral=True)
            return
        
        self.config_service.set_setting(self.key, value, interaction.user.id)
        await interaction.response.send_message(f"✅ Setting updated to: `{value}`", ephemeral=True)


class SetTextModal(discord.ui.Modal):
    def __init__(self, config_service, key: str, title: str):
        super().__init__(title=title, timeout=300)
        self.config_service = config_service
        self.key = key
        
        current = config_service.get_setting(key, "")
        self.value_input = discord.ui.TextInput(
            label="Value",
            placeholder=f"Enter value (current: {current})",
            style=discord.TextStyle.short,
            required=True,
            max_length=200,
            default=current
        )
        self.add_item(self.value_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        value = self.value_input.value.strip()
        self.config_service.set_setting(self.key, value, interaction.user.id)
        await interaction.response.send_message(f"✅ Setting updated to: `{value}`", ephemeral=True)


class SetLongTextModal(discord.ui.Modal):
    def __init__(self, config_service, key: str, title: str):
        super().__init__(title=title, timeout=300)
        self.config_service = config_service
        self.key = key
        
        current = config_service.get_setting(key, "")
        self.value_input = discord.ui.TextInput(
            label="Value",
            placeholder=f"Enter value (current: {current[:50]}...)",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000,
            default=current
        )
        self.add_item(self.value_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        value = self.value_input.value.strip()
        self.config_service.set_setting(self.key, value, interaction.user.id)
        await interaction.response.send_message(f"✅ Setting updated", ephemeral=True)


class SetIntSettingButton(discord.ui.Button):
    def __init__(self, config_service, key: str, value: int):
        super().__init__(label=f"Set {key}", style=discord.ButtonStyle.primary, emoji="🔢", row=2)
        self.config_service = config_service
        self.key = key
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetIntModal(self.config_service, self.key, f"Set {key}")
        await interaction.response.send_modal(modal)


class SetListSettingButton(discord.ui.Button):
    def __init__(self, config_service, key: str, value: list):
        super().__init__(label=f"Set {key}", style=discord.ButtonStyle.primary, emoji="📋", row=3)
        self.config_service = config_service
        self.key = key
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetTextModal(self.config_service, self.key, f"Set {key} (comma-separated)")
        await interaction.response.send_modal(modal)


class SetLongTextButton(discord.ui.Button):
    def __init__(self, config_service, key: str, value: str):
        super().__init__(label=f"Set {key}", style=discord.ButtonStyle.primary, emoji="📝", row=3)
        self.config_service = config_service
        self.key = key
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetLongTextModal(self.config_service, self.key, f"Set {key}")
        await interaction.response.send_modal(modal)


class SetTextSettingButton(discord.ui.Button):
    def __init__(self, config_service, key: str, value: str):
        super().__init__(label=f"Set {key}", style=discord.ButtonStyle.primary, emoji="📝", row=4)
        self.config_service = config_service
        self.key = key
    
    async def callback(self, interaction: discord.Interaction):
        modal = SetTextModal(self.config_service, self.key, f"Set {key}")
        await interaction.response.send_modal(modal)


class SetRoleModal(discord.ui.Modal):
    def __init__(self, config_service, key: str, title: str):
        super().__init__(title=title, timeout=300)
        self.config_service = config_service
        self.key = key
        
        current = config_service.get_setting(key, 0)
        self.value_input = discord.ui.TextInput(
            label="Role ID",
            placeholder=f"Enter role ID (current: {current})",
            style=discord.TextStyle.short,
            required=True,
            max_length=20,
            default=str(current) if current else ""
        )
        self.add_item(self.value_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        value = self.value_input.value.strip()
        if value:
            try:
                role_id = int(value)
            except ValueError:
                await interaction.response.send_message("❌ Please enter a valid role ID.", ephemeral=True)
                return
        else:
            role_id = None
        
        self.config_service.set_setting(self.key, role_id, interaction.user.id)
        await interaction.response.send_message(f"✅ Role ID updated", ephemeral=True)


class SetChannelModal(discord.ui.Modal):
    def __init__(self, config_service, key: str, title: str):
        super().__init__(title=title, timeout=300)
        self.config_service = config_service
        self.key = key
        
        current = config_service.get_setting(key, 0)
        self.value_input = discord.ui.TextInput(
            label="Channel ID",
            placeholder=f"Enter channel ID (current: {current})",
            style=discord.TextStyle.short,
            required=True,
            max_length=20,
            default=str(current) if current else ""
        )
        self.add_item(self.value_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        value = self.value_input.value.strip()
        if value:
            try:
                channel_id = int(value)
            except ValueError:
                await interaction.response.send_message("❌ Please enter a valid channel ID.", ephemeral=True)
                return
        else:
            channel_id = None
        
        self.config_service.set_setting(self.key, channel_id, interaction.user.id)
        await interaction.response.send_message(f"✅ Channel ID updated", ephemeral=True)