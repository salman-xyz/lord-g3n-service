import discord
from typing import List
from sqlalchemy import func
from database import Code, Service

class CodeSelect(discord.ui.Select):
    def __init__(self, ticket_service, config_service, codes: List[Code]):
        options = []
        for code in codes[:25]:
            service_name = code.service.name if code.service else "Unknown"
            options.append(discord.SelectOption(
                label=f"{code.code}",
                description=f"{service_name} ({code.category})",
                value=str(code.id)
            ))
        
        super().__init__(
            placeholder="Select a code to redeem...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="code_select"
        )
        self.ticket_service = ticket_service
        self.config_service = config_service
        self.codes = {str(c.id): c for c in codes}
    
    async def callback(self, interaction: discord.Interaction):
        code_id = int(self.values[0])
        code = self.codes.get(str(code_id))
        
        if not code:
            await interaction.response.send_message("❌ Code not found.", ephemeral=True)
            return
        
        if self.ticket_service.has_active_ticket_for_code(interaction.user.id, code.id):
            await interaction.response.send_message("❌ You already have an active ticket for this code.", ephemeral=True)
            return
        
        from views.ticket_panel import TicketTypeSelect
        await TicketTypeSelect.create_ticket(self, interaction, code)

class CodeSelectView(discord.ui.View):
    def __init__(self, ticket_service, config_service, codes: List[Code]):
        super().__init__(timeout=60)
        self.add_item(CodeSelect(ticket_service, config_service, codes))


class RedeemCodeModal(discord.ui.Modal):
    def __init__(self, ticket_service, config_service, panel_view):
        super().__init__(title="Redeem Code", timeout=300)
        self.ticket_service = ticket_service
        self.config_service = config_service
        self.panel_view = panel_view
        
        self.code_input = discord.ui.TextInput(
            label="Redemption Code",
            placeholder="e.g. ABC123DEF",
            style=discord.TextStyle.short,
            required=True,
            max_length=20,
            min_length=3
        )
        self.add_item(self.code_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        # Check ticket limit (verification already done in handle_redeem_ticket)
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
        
        await interaction.response.defer(ephemeral=True)
        
        code_str = self.code_input.value.strip().upper()
        
        from database import get_db
        db = next(get_db())
        try:
            # Find code by value (case-insensitive)
            from sqlalchemy import func
            code = db.query(Code).filter(
                Code.guild_id == interaction.guild.id,
                func.upper(Code.code) == code_str,
                Code.status == "unused"
            ).first()
            
            if not code:
                embed = discord.Embed(
                    title="Invalid Code",
                    description=f"The code `{code_str}` is invalid or has already been used.",
                    color=0xE74C3C
                )
                embed.set_footer(text="Lord G3N Services")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Check if code belongs to user
            if code.discord_id != interaction.user.id:
                embed = discord.Embed(
                    title="Code Mismatch",
                    description="This redemption code does not belong to you.",
                    color=0xE74C3C
                )
                embed.set_footer(text="Lord G3N Services")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Check for active ticket
            if self.ticket_service.has_active_ticket_for_code(interaction.user.id, code.id):
                embed = discord.Embed(
                    title="Active Ticket Exists",
                    description="You already have an open ticket for this code.",
                    color=0xE74C3C
                )
                embed.set_footer(text="Lord G3N Services")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create ticket
            await self.panel_view.create_ticket_from_modal(interaction, code)
        finally:
            db.close()


class RedeemCodeButtonView(discord.ui.View):
    def __init__(self, ticket_service, config_service, panel_view):
        super().__init__(timeout=300)
        self.ticket_service = ticket_service
        self.config_service = config_service
        self.panel_view = panel_view