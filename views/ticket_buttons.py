import discord
from typing import Optional
from services.ticket_service import TicketService

class TicketButtonsView(discord.ui.View):
    def __init__(self, ticket_service: TicketService, ticket, staff_role_id: int = None):
        super().__init__(timeout=None)
        self.ticket_service = ticket_service
        self.ticket = ticket
        self.staff_role_id = staff_role_id
        
        self.add_item(DeleteTicketButton(ticket_service, ticket, staff_role_id))
        self.add_item(DeleteWithReasonButton(ticket_service, ticket, staff_role_id))


class DeleteTicketButton(discord.ui.Button):
    def __init__(self, ticket_service: TicketService, ticket, staff_role_id: int = None):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Delete",
            custom_id=f"delete_ticket_{ticket.id}",
            row=0
        )
        self.ticket_service = ticket_service
        self.ticket = ticket
        self.staff_role_id = staff_role_id
    
    async def callback(self, interaction: discord.Interaction):
        if self.staff_role_id:
            staff_role = interaction.guild.get_role(self.staff_role_id)
            if not staff_role or staff_role not in interaction.user.roles:
                if not interaction.user.guild_permissions.manage_channels:
                    await interaction.response.send_message("❌ You don't have permission to use this button.", ephemeral=True)
                    return
        elif not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You don't have permission to use this button.", ephemeral=True)
            return
        
        await interaction.response.send_message("🗑️ Ticket will be deleted in 3 seconds...", ephemeral=False)
        
        log_channel_id = self.ticket_service.get_ticket_log_channel_id()
        deleted_ticket = self.ticket_service.close_ticket(
            self.ticket.id, 
            interaction.user.id, 
            "Deleted by staff"
        )
        
        if log_channel_id:
            log_channel = interaction.guild.get_channel(log_channel_id)
            if log_channel:
                try:
                    embed = discord.Embed(
                        title="🗑️ Ticket Deleted",
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="User", value=f"<@{self.ticket.discord_id}>", inline=False)
                    embed.add_field(name="Category", value=self.ticket.category or "N/A", inline=True)
                    embed.add_field(name="Service", value=self.ticket.service or "N/A", inline=True)
                    embed.add_field(name="Deleted By", value=interaction.user.mention, inline=False)
                    embed.add_field(name="Reason", value="No reason provided", inline=False)
                    embed.set_footer(text=f"Ticket ID: {self.ticket.id}")
                    await log_channel.send(embed=embed)
                except Exception as e:
                    print(f"Failed to log deletion: {e}")
        
        import asyncio
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete(reason=f"Ticket deleted by {interaction.user}")
        except Exception as e:
            print(f"Failed to delete channel: {e}")


class DeleteWithReasonButton(discord.ui.Button):
    def __init__(self, ticket_service: TicketService, ticket, staff_role_id: int = None):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Delete with Reason",
            custom_id=f"delete_reason_{ticket.id}",
            row=0
        )
        self.ticket_service = ticket_service
        self.ticket = ticket
        self.staff_role_id = staff_role_id
    
    async def callback(self, interaction: discord.Interaction):
        if self.staff_role_id:
            staff_role = interaction.guild.get_role(self.staff_role_id)
            if not staff_role or staff_role not in interaction.user.roles:
                if not interaction.user.guild_permissions.manage_channels:
                    await interaction.response.send_message("❌ You don't have permission to use this button.", ephemeral=True)
                    return
        elif not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You don't have permission to use this button.", ephemeral=True)
            return
        
        log_channel_id = self.ticket_service.get_ticket_log_channel_id()
        from views.delete_modal import DeleteReasonModal
        modal = DeleteReasonModal(self.ticket_service, self.ticket, log_channel_id, interaction.client)
        await interaction.response.send_modal(modal)


class PersistentDeleteTicketButton(discord.ui.Button):
    """Persistent button that works after bot restart"""
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Delete",
            custom_id="persistent_delete_ticket",
            row=0
        )
    
    async def callback(self, interaction: discord.Interaction):
        from database import get_db, Ticket
        from services.ticket_service import TicketService
        
        db = next(get_db())
        try:
            ticket = db.query(Ticket).filter(
                Ticket.guild_id == interaction.guild.id,
                Ticket.channel_id == interaction.channel.id,
                Ticket.status == "open"
            ).first()
            
            if not ticket:
                await interaction.response.send_message("❌ No active ticket found in this channel.", ephemeral=True)
                return
            
            ticket_service = TicketService(db, interaction.guild.id)
            staff_role_id = ticket_service.get_staff_role_id()
            
            if staff_role_id:
                staff_role = interaction.guild.get_role(staff_role_id)
                if not staff_role or staff_role not in interaction.user.roles:
                    if not interaction.user.guild_permissions.manage_channels:
                        await interaction.response.send_message("❌ You don't have permission to use this button.", ephemeral=True)
                        return
            elif not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("❌ You don't have permission to use this button.", ephemeral=True)
                return
            
            await interaction.response.send_message("🗑️ Ticket will be deleted in 3 seconds...", ephemeral=False)
            
            log_channel_id = ticket_service.get_ticket_log_channel_id()
            deleted_ticket = ticket_service.close_ticket(
                ticket.id, 
                interaction.user.id, 
                "Deleted by staff"
            )
            
            if log_channel_id:
                log_channel = interaction.guild.get_channel(log_channel_id)
                if log_channel:
                    try:
                        embed = discord.Embed(
                            title="🗑️ Ticket Deleted",
                            color=discord.Color.red(),
                            timestamp=discord.utils.utcnow()
                        )
                        embed.add_field(name="User", value=f"<@{ticket.discord_id}>", inline=False)
                        embed.add_field(name="Category", value=ticket.category or "N/A", inline=True)
                        embed.add_field(name="Service", value=ticket.service or "N/A", inline=True)
                        embed.add_field(name="Deleted By", value=interaction.user.mention, inline=False)
                        embed.add_field(name="Reason", value="No reason provided", inline=False)
                        embed.set_footer(text=f"Ticket ID: {ticket.id}")
                        await log_channel.send(embed=embed)
                    except Exception as e:
                        print(f"Failed to log deletion: {e}")
            
            import asyncio
            await asyncio.sleep(3)
            try:
                await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
            except Exception as e:
                print(f"Failed to delete channel: {e}")
        finally:
            db.close()


class PersistentDeleteWithReasonButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Delete with Reason",
            custom_id="persistent_delete_reason",
            row=0
        )
    
    async def callback(self, interaction: discord.Interaction):
        from database import get_db, Ticket
        from services.ticket_service import TicketService
        from views.delete_modal import DeleteReasonModal
        
        db = next(get_db())
        try:
            ticket = db.query(Ticket).filter(
                Ticket.guild_id == interaction.guild.id,
                Ticket.channel_id == interaction.channel.id,
                Ticket.status == "open"
            ).first()
            
            if not ticket:
                await interaction.response.send_message("❌ No active ticket found in this channel.", ephemeral=True)
                return
            
            ticket_service = TicketService(db, interaction.guild.id)
            staff_role_id = ticket_service.get_staff_role_id()
            
            if staff_role_id:
                staff_role = interaction.guild.get_role(staff_role_id)
                if not staff_role or staff_role not in interaction.user.roles:
                    if not interaction.user.guild_permissions.manage_channels:
                        await interaction.response.send_message("❌ You don't have permission to use this button.", ephemeral=True)
                        return
            elif not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("❌ You don't have permission to use this button.", ephemeral=True)
                return
            
            log_channel_id = ticket_service.get_ticket_log_channel_id()
            modal = DeleteReasonModal(ticket_service, ticket, log_channel_id, interaction.client)
            await interaction.response.send_modal(modal)
        finally:
            db.close()


class PersistentTicketButtonsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PersistentDeleteTicketButton())
        self.add_item(PersistentDeleteWithReasonButton())
    
    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="persistent_delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("This button requires ticket context. Please use the ticket panel.", ephemeral=True)

    @discord.ui.button(label="Delete with Reason", style=discord.ButtonStyle.danger, custom_id="persistent_delete_reason")
    async def delete_with_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("This button requires ticket context. Please use the ticket panel.", ephemeral=True)


class RedeemTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="redeem_ticket_delete")
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please use active ticket view.", ephemeral=True)


class GeneralTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="general_ticket_view")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please use the ticket panel to create a ticket.", ephemeral=True)