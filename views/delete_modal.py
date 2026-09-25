import discord
from typing import Optional

class DeleteReasonModal(discord.ui.Modal):
    def __init__(self, ticket_service, ticket, log_channel_id: int = None, bot=None):
        super().__init__(title="Delete Ticket", timeout=300)
        self.ticket_service = ticket_service
        self.ticket = ticket
        self.log_channel_id = log_channel_id
        self.bot = bot
        
        self.reason_input = discord.ui.TextInput(
            label="Reason",
            placeholder="Enter the reason for deleting this ticket...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.reason_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value.strip()
        
        if not reason:
            await interaction.response.send_message("❌ Reason is required.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        deleted_ticket = self.ticket_service.close_ticket(
            self.ticket.id, 
            interaction.user.id, 
            reason
        )
        
        if not deleted_ticket:
            await interaction.followup.send("❌ Failed to close ticket.", ephemeral=True)
            return
        
        log_channel = None
        if self.log_channel_id:
            log_channel = interaction.guild.get_channel(self.log_channel_id)
        
        if log_channel:
            try:
                embed = discord.Embed(
                    title="🗑️ Ticket Deleted",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="User", value=f"<@{deleted_ticket.discord_id}> (`{deleted_ticket.discord_id}`)", inline=False)
                embed.add_field(name="Category", value=deleted_ticket.category or "N/A", inline=True)
                embed.add_field(name="Service", value=deleted_ticket.service or "N/A", inline=True)
                embed.add_field(name="Deleted By", value=f"<@{interaction.user.id}>", inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Ticket Created", value=deleted_ticket.created_at.strftime("%d %b %Y %H:%M") if deleted_ticket.created_at else "Unknown", inline=True)
                embed.add_field(name="Ticket Deleted", value=discord.utils.utcnow().strftime("%d %b %Y %H:%M"), inline=True)
                embed.set_footer(text=f"Ticket ID: {deleted_ticket.id}")
                await log_channel.send(embed=embed)
            except Exception as e:
                print(f"Failed to send log: {e}")
        
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}: {reason}")
        except Exception as e:
            print(f"Failed to delete channel: {e}")
            await interaction.followup.send(f"Ticket closed but failed to delete channel: {e}", ephemeral=True)

class DeleteConfirmView(discord.ui.View):
    def __init__(self, ticket_service, ticket, log_channel_id: int = None, bot=None, reason_required: bool = True):
        super().__init__(timeout=60)
        self.ticket_service = ticket_service
        self.ticket = ticket
        self.log_channel_id = log_channel_id
        self.bot = bot
        self.reason_required = reason_required
    
    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.reason_required:
            modal = DeleteReasonModal(self.ticket_service, self.ticket, self.log_channel_id, self.bot)
            await interaction.response.send_modal(modal)
        else:
            await self.delete_without_reason(interaction)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Deletion cancelled.", embed=None, view=None)
    
    async def delete_without_reason(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        deleted_ticket = self.ticket_service.close_ticket(
            self.ticket.id, 
            interaction.user.id, 
            "No reason provided"
        )
        
        if not deleted_ticket:
            await interaction.followup.send("❌ Failed to close ticket.", ephemeral=True)
            return
        
        log_channel = None
        if self.log_channel_id:
            log_channel = interaction.guild.get_channel(self.log_channel_id)
        
        if log_channel:
            try:
                embed = discord.Embed(
                    title="🗑️ Ticket Deleted",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="User", value=f"<@{deleted_ticket.discord_id}> (`{deleted_ticket.discord_id}`)", inline=False)
                embed.add_field(name="Category", value=deleted_ticket.category or "N/A", inline=True)
                embed.add_field(name="Service", value=deleted_ticket.service or "N/A", inline=True)
                embed.add_field(name="Deleted By", value=f"<@{interaction.user.id}>", inline=False)
                embed.add_field(name="Reason", value="No reason provided", inline=False)
                embed.add_field(name="Ticket Created", value=deleted_ticket.created_at.strftime("%d %b %Y %H:%M") if deleted_ticket.created_at else "Unknown", inline=True)
                embed.add_field(name="Ticket Deleted", value=discord.utils.utcnow().strftime("%d %b %Y %H:%M"), inline=True)
                embed.set_footer(text=f"Ticket ID: {deleted_ticket.id}")
                await log_channel.send(embed=embed)
            except Exception as e:
                print(f"Failed to send log: {e}")
        
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except Exception as e:
            print(f"Failed to delete channel: {e}")
            await interaction.followup.send(f"Ticket closed but failed to delete channel: {e}", ephemeral=True)