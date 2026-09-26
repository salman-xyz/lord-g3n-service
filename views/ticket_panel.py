import discord
from typing import Optional
from config import TICKET_TYPES


def build_ticket_panel_embed(guild_id: int, config_service=None, guild_name: str = None) -> discord.Embed:
    gif_url = None
    if config_service:
        gif_url = config_service.get_setting("ticket_gif_url")
    
    server_title = guild_name or "Lord G3N Services"
    
    desc = (
        "Select a ticket type below to create a ticket.\n\n"
        "**Available Ticket Types:**\n"
        "• 🎟️ **Redeem**: Use a generated service code\n"
        "• 🎁 **Reward**: Open a Ticket to claim Rewards\n"
        "• 🛒 **Purchase**: Buy products/services\n"
        "• ⚠️ **Report**: Report issues or users\n"
        "• 🤝 **Partnership**: Open a Ticket for Partnership with us"
    )
    
    embed = discord.Embed(
        title=f"🏷️ {server_title} Ticket Control",
        description=desc,
        color=discord.Color.green()
    )
    
    if gif_url:
        embed.set_image(url=gif_url)
        
    embed.set_footer(text=f"{server_title} | Ticket System")
    return embed


class TicketTypeSelect(discord.ui.Select):
    def __init__(self, ticket_service, config_service, verification_service):
        options = []
        for key, data in TICKET_TYPES.items():
            options.append(discord.SelectOption(
                label=data["label"],
                description=data["description"],
                emoji=data["emoji"],
                value=key
            ))
        
        super().__init__(
            placeholder="Select Ticket Type",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_type_select"
        )
        self.ticket_service = ticket_service
        self.config_service = config_service
        self.verification_service = verification_service
    
    async def callback(self, interaction: discord.Interaction):
        ticket_type = self.values[0]
        
        if ticket_type == "redeem":
            await self.handle_redeem_ticket(interaction)
        elif ticket_type == "reward":
            await self.handle_reward_ticket(interaction)
        elif ticket_type == "purchase":
            await self.handle_purchase_ticket(interaction)
        elif ticket_type == "report":
            await self.handle_report_ticket(interaction)
        elif ticket_type == "partnership":
            await self.handle_partnership_ticket(interaction)
        elif ticket_type == "support":
            await self.handle_support_ticket(interaction)
    
    async def handle_redeem_ticket(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        # Try to consume an unused verification
        from database import get_db, VerificationSubmission
        db = next(get_db())
        try:
            # Find unused verification for this user
            verification = db.query(VerificationSubmission).filter(
                VerificationSubmission.guild_id == interaction.guild.id,
                VerificationSubmission.discord_id == user_id,
                VerificationSubmission.status == "processed",
                VerificationSubmission.used == False
            ).first()
            
            if not verification:
                # No unused verification - require new verification
                embed = discord.Embed(
                    title="Verification Required",
                    description="You must complete the verification form for each ticket.\n\nFill out the Google Form, then try creating a ticket again.",
                    color=0xE74C3C
                )
                embed.set_footer(text="Lord G3N Services  •  One verification per ticket")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Mark verification as used (will be linked to ticket after creation)
            verification.used = True
            db.commit()
            
        finally:
            db.close()
        
        # Check ticket limit
        can_create, msg = self.ticket_service.can_create_ticket(user_id, interaction.guild)
        if not can_create:
            embed = discord.Embed(
                title="Ticket Limit Reached",
                description=msg,
                color=0xE74C3C
            )
            embed.set_footer(text="Lord G3N Services")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Show modal directly to enter code
        from views.redeem_view import RedeemCodeModal
        modal = RedeemCodeModal(self.ticket_service, self.config_service, self)
        await interaction.response.send_modal(modal)
    
    async def create_ticket(self, interaction: discord.Interaction, code):
        await interaction.response.defer(ephemeral=True)
        await self._create_ticket(interaction, code)

    async def create_ticket_from_modal(self, interaction: discord.Interaction, code):
        # Interaction already deferred by modal, use followup
        await self._create_ticket(interaction, code)

    async def _create_ticket(self, interaction: discord.Interaction, code):
        category_id = self.ticket_service.get_ticket_category_id("redeem")
        category = interaction.guild.get_channel(category_id) if category_id else None
        
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("❌ Ticket category not configured properly.", ephemeral=True)
            return
        
        name_format = self.ticket_service.get_ticket_name_format()
        channel_name = name_format.format(
            type="redeem",
            username=interaction.user.name,
            user_id=interaction.user.id
        )
        channel_name = channel_name.lower().replace(" ", "-")[:100]
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True),
        }
        
        staff_role_id = self.ticket_service.get_staff_role_id()
        if staff_role_id:
            staff_role = interaction.guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        try:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Redeem ticket for {interaction.user} (Code: {code.code})"
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to create ticket channel: {e}", ephemeral=True)
            return
        
        ticket = self.ticket_service.create_ticket(
            channel.id,
            interaction.user.id,
            "redeem",
            category=code.category,
            service=code.service.name if code.service else None,
            code_id=code.id
        )
        
        # Link the used verification to this ticket
        from database import get_db, VerificationSubmission
        db = next(get_db())
        try:
            verification = db.query(VerificationSubmission).filter(
                VerificationSubmission.guild_id == interaction.guild.id,
                VerificationSubmission.discord_id == interaction.user.id,
                VerificationSubmission.used == True,
                VerificationSubmission.used_for_ticket_id == None
            ).first()
            if verification:
                verification.used_for_ticket_id = ticket.id
                db.commit()
        finally:
            db.close()
        
        staff_role_id = self.ticket_service.get_staff_role_id()
        staff_mention = f"<@&{staff_role_id}>" if staff_role_id else "@staff"
        
        welcome_desc = (
            f"Welcome {interaction.user.mention},\n"
            f"Staff: {staff_mention}\n\n"
            f"**Please wait until our support team assists you shortly.**"
        )
        
        from views.ticket_buttons import TicketButtonsView
        view = TicketButtonsView(self.ticket_service, ticket, staff_role_id)
        
        embed = discord.Embed(
            description=welcome_desc,
            color=0x2F3136
        )
        embed.add_field(name="Category", value=f"`{code.category}`", inline=True)
        embed.add_field(name="Service", value=f"`{code.service.name if code.service else 'Unknown'}`", inline=True)
        embed.set_footer(text="Powered by Lord G3N Services")
        
        try:
            await channel.send(content=f"{interaction.user.mention} {staff_mention}", embed=embed, view=view)
        except Exception as e:
            print(f"Failed to send welcome message: {e}")
        
        self.ticket_service.log_ticket_action("ticket_created", interaction.user.id, ticket_id=ticket.id, details=f"Redeem ticket for {code.code}")
        
        success_embed = discord.Embed(
            description=f"Your ticket has been created: {channel.mention}",
            color=0x2ECC71
        )
        success_embed.set_footer(text="Lord G3N Services")
        await interaction.followup.send(embed=success_embed, ephemeral=True)
    
    async def handle_rewards_ticket(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        await interaction.response.defer(ephemeral=True)
        
        can_create, msg = self.ticket_service.can_create_ticket(user_id, interaction.guild)
        if not can_create:
            embed = discord.Embed(
                title="Ticket Limit Reached",
                description=msg,
                color=0xE74C3C
            )
            embed.set_footer(text="Lord G3N Services")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        category_id = self.ticket_service.get_ticket_category_id("rewards")
        category = interaction.guild.get_channel(category_id) if category_id else None
        
        if not category or not isinstance(category, discord.CategoryChannel):
            embed = discord.Embed(
                description="Rewards ticket category is not configured. Please contact an administrator.",
                color=0xE74C3C
            )
            embed.set_footer(text="Lord G3N Services")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        name_format = self.ticket_service.get_ticket_name_format()
        channel_name = name_format.format(
            type="rewards",
            username=interaction.user.name,
            user_id=interaction.user.id
        )
        channel_name = channel_name.lower().replace(" ", "-")[:100]
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True),
        }
        
        staff_role_id = self.ticket_service.get_staff_role_id()
        if staff_role_id:
            staff_role = interaction.guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        try:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Rewards ticket for {interaction.user}"
            )
        except Exception as e:
            embed = discord.Embed(
                description=f"Failed to create ticket channel: {e}",
                color=0xE74C3C
            )
            embed.set_footer(text="Lord G3N Services")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        ticket = self.ticket_service.create_ticket(
            channel.id,
            interaction.user.id,
            "rewards",
            category="rewards",
            service="claim rewards"
        )
        
        welcome_msg = self.ticket_service.get_welcome_message()
        welcome_msg = welcome_msg.format(
            user_mention=interaction.user.mention,
            category="rewards",
            service="claim rewards"
        )
        
        from views.ticket_buttons import TicketButtonsView
        view = TicketButtonsView(self.ticket_service, ticket, staff_role_id)
        
        embed = discord.Embed(
            description=welcome_msg,
            color=0xF39C12
        )
        embed.set_author(name="Rewards Ticket", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Lord G3N Services  •  Support Team will assist you shortly")
        embed.timestamp = discord.utils.utcnow()
        
        try:
            await channel.send(content=interaction.user.mention, embed=embed, view=view)
        except Exception as e:
            print(f"Failed to send welcome message: {e}")
        
        self.ticket_service.log_ticket_action("ticket_created", interaction.user.id, ticket_id=ticket.id, details="Rewards ticket")
        
        success_embed = discord.Embed(
            description=f"Your rewards ticket has been created: {channel.mention}",
            color=0xF39C12
        )
        success_embed.set_footer(text="Lord G3N Services")
        await interaction.followup.send(embed=success_embed, ephemeral=True)
    
    async def handle_support_ticket(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        await interaction.response.defer(ephemeral=True)
        
        can_create, msg = self.ticket_service.can_create_ticket(user_id, interaction.guild)
        if not can_create:
            embed = discord.Embed(
                title="Ticket Limit Reached",
                description=msg,
                color=0xE74C3C
            )
            embed.set_footer(text="Lord G3N Services")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        category_id = self.ticket_service.get_ticket_category_id("support")
        category = interaction.guild.get_channel(category_id) if category_id else None
        
        if not category or not isinstance(category, discord.CategoryChannel):
            embed = discord.Embed(
                description="Support ticket category is not configured. Please contact an administrator.",
                color=0xE74C3C
            )
            embed.set_footer(text="Lord G3N Services")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        name_format = self.ticket_service.get_ticket_name_format()
        channel_name = name_format.format(
            type="support",
            username=interaction.user.name,
            user_id=interaction.user.id
        )
        channel_name = channel_name.lower().replace(" ", "-")[:100]
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True),
        }
        
        staff_role_id = self.ticket_service.get_staff_role_id()
        if staff_role_id:
            staff_role = interaction.guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        try:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Support ticket for {interaction.user}"
            )
        except Exception as e:
            embed = discord.Embed(
                description=f"Failed to create ticket channel: {e}",
                color=0xE74C3C
            )
            embed.set_footer(text="Lord G3N Services")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        ticket = self.ticket_service.create_ticket(
            channel.id,
            interaction.user.id,
            "support",
            category="support",
            service="general support"
        )
        
        welcome_msg = self.ticket_service.get_welcome_message()
        welcome_msg = welcome_msg.format(
            user_mention=interaction.user.mention,
            category="support",
            service="general support"
        )
        
        from views.ticket_buttons import TicketButtonsView
        view = TicketButtonsView(self.ticket_service, ticket, staff_role_id)
        
        embed = discord.Embed(
            description=welcome_msg,
            color=0x3498DB
        )
        embed.set_author(name="Support Ticket", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Lord G3N Services  •  Support Team will assist you shortly")
        embed.timestamp = discord.utils.utcnow()
        
        try:
            await channel.send(content=interaction.user.mention, embed=embed, view=view)
        except Exception as e:
            print(f"Failed to send welcome message: {e}")
        
        self.ticket_service.log_ticket_action("ticket_created", interaction.user.id, ticket_id=ticket.id, details="Support ticket")
        
        success_embed = discord.Embed(
            description=f"Your support ticket has been created: {channel.mention}",
            color=0x3498DB
        )
        success_embed.set_footer(text="Lord G3N Services")
        await interaction.followup.send(embed=success_embed, ephemeral=True)
        
        from views.ticket_buttons import TicketButtonsView
        view = TicketButtonsView(self.ticket_service, ticket, staff_role_id)
        
        embed = discord.Embed(
            description=welcome_msg,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Powered by Lord G3N Services")
        
        try:
            await channel.send(content=interaction.user.mention, embed=embed, view=view)
        except Exception as e:
            print(f"Failed to send welcome message: {e}")
        
        self.ticket_service.log_ticket_action("ticket_created", interaction.user.id, ticket_id=ticket.id, details="Support ticket")
        await interaction.followup.send(f"✅ Ticket created: {channel.mention}", ephemeral=True)
    
    async def handle_reward_ticket(self, interaction: discord.Interaction):
        await self._create_generic_ticket(interaction, "reward", "Reward", "claim rewards", 0xF39C12)
    
    async def handle_purchase_ticket(self, interaction: discord.Interaction):
        await self._create_generic_ticket(interaction, "purchase", "Purchase", "buy products", 0x9B59B6)
    
    async def handle_report_ticket(self, interaction: discord.Interaction):
        await self._create_generic_ticket(interaction, "report", "Report", "report issue", 0xE74C3C)
    
    async def handle_partnership_ticket(self, interaction: discord.Interaction):
        await self._create_generic_ticket(interaction, "partnership", "Partnership", "partnership inquiry", 0x1ABC9C)
    
    async def _create_generic_ticket(self, interaction: discord.Interaction, ticket_type: str, display_name: str, service: str, color: int):
        user_id = interaction.user.id
        
        await interaction.response.defer(ephemeral=True)
        
        can_create, msg = self.ticket_service.can_create_ticket(user_id, interaction.guild)
        if not can_create:
            embed = discord.Embed(
                title="Ticket Limit Reached",
                description=msg,
                color=0xE74C3C
            )
            embed.set_footer(text="Lord G3N Services")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        category_id = self.ticket_service.get_ticket_category_id(ticket_type)
        category = interaction.guild.get_channel(category_id) if category_id else None
        
        if not category or not isinstance(category, discord.CategoryChannel):
            embed = discord.Embed(
                description=f"{display_name} ticket category is not configured. Please contact an administrator.",
                color=0xE74C3C
            )
            embed.set_footer(text="Lord G3N Services")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        name_format = self.ticket_service.get_ticket_name_format()
        channel_name = name_format.format(
            type=ticket_type,
            username=interaction.user.name,
            user_id=interaction.user.id
        )
        channel_name = channel_name.lower().replace(" ", "-")[:100]
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True),
        }
        
        staff_role_id = self.ticket_service.get_staff_role_id()
        if staff_role_id:
            staff_role = interaction.guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        try:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"{display_name} ticket for {interaction.user}"
            )
        except Exception as e:
            embed = discord.Embed(
                description=f"Failed to create ticket channel: {e}",
                color=0xE74C3C
            )
            embed.set_footer(text="Lord G3N Services")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        ticket = self.ticket_service.create_ticket(
            channel.id,
            interaction.user.id,
            ticket_type,
            category=ticket_type,
            service=service
        )
        
        staff_role_id = self.ticket_service.get_staff_role_id()
        staff_mention = f"<@&{staff_role_id}>" if staff_role_id else "@staff"
        
        welcome_desc = (
            f"Welcome {interaction.user.mention},\n"
            f"Staff: {staff_mention}\n\n"
            f"**Please wait until our support team assists you shortly.**"
        )
        
        from views.ticket_buttons import TicketButtonsView
        view = TicketButtonsView(self.ticket_service, ticket, staff_role_id)
        
        embed = discord.Embed(
            description=welcome_desc,
            color=0x2F3136
        )
        embed.add_field(name="Category", value=f"`{ticket_type}`", inline=True)
        embed.add_field(name="Service", value=f"`{service}`", inline=True)
        embed.set_footer(text="Powered by Lord G3N Services")
        
        try:
            await channel.send(content=f"{interaction.user.mention} {staff_mention}", embed=embed, view=view)
        except Exception as e:
            print(f"Failed to send welcome message: {e}")
        
        self.ticket_service.log_ticket_action("ticket_created", interaction.user.id, ticket_id=ticket.id, details=f"{display_name} ticket")
        
        success_embed = discord.Embed(
            description=f"Your {display_name.lower()} ticket has been created: {channel.mention}",
            color=color
        )
        success_embed.set_footer(text="Lord G3N Services")
        await interaction.followup.send(embed=success_embed, ephemeral=True)


class TicketPanelView(discord.ui.View):
    def __init__(self, ticket_service, config_service, verification_service):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect(ticket_service, config_service, verification_service))

class PersistentTicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.select(
        placeholder="Select Ticket Type",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Redeem a Code", description="Redeem your generated service code", emoji="🎟️", value="redeem"),
            discord.SelectOption(label="Reward", description="Claim rewards and related issues", emoji="🎁", value="reward"),
            discord.SelectOption(label="Purchase", description="Buy products or services", emoji="🛒", value="purchase"),
            discord.SelectOption(label="Report", description="Report users or issues", emoji="⚠️", value="report"),
            discord.SelectOption(label="Partnership", description="Partnership inquiries", emoji="🤝", value="partnership"),
        ],
        custom_id="persistent_ticket_type_select"
    )
    async def ticket_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_message("Please use the active ticket panel with proper services configured.", ephemeral=True)