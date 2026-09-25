import discord
from discord.ext import commands

from database import get_db
from views.ticket_panel import TicketPanelView, build_ticket_panel_embed
from services.ticket_service import TicketService
from services.configuration_service import ConfigurationService
from services.verification_service import VerificationService

class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ticketpanels')
    @commands.has_permissions(administrator=True)
    async def ticketpanels_command(self, ctx):
        """Send the ticket panel"""
        db = next(get_db())
        try:
            ticket_service = TicketService(db, ctx.guild.id)
            config_service = ConfigurationService(db, ctx.guild.id)
            verification_service = VerificationService(db, ctx.guild.id)
            embed = build_ticket_panel_embed(ctx.guild.id, config_service, ctx.guild.name if ctx.guild else None)
            view = TicketPanelView(ticket_service, config_service, verification_service)
            await ctx.send(embed=embed, view=view)
        finally:
            db.close()

async def setup(bot):
    await bot.add_cog(TicketsCog(bot))
