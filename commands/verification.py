import discord
from discord.ext import commands

from services.verification_service import check_verification, unverify_user, get_user_stats, get_user_by_discord_id
from services.google_sheets import process_sheet_for_guild
from services.logging_service import create_log_entry

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='verify')
    async def verify_command(self, ctx, member: discord.Member = None):
        """Check verification status. Admins can check others."""
        target = member or ctx.author
        
        if member and member != ctx.author:
            if not ctx.author.guild_permissions.administrator:
                # Basic check; could be extended to allow staff_role
                await ctx.send("❌ You don't have permission to check other users.")
                return

        msg = await ctx.send(f"🔎 Checking {'your' if target == ctx.author else target.name + '''\\'s'''} verification...")
        
        user = await check_verification(ctx.guild.id, target.id, target.name)
        if user.get('verified', False):
            embed = discord.Embed(title="✅ Verified", color=discord.Color.green())
            embed.add_field(name="User", value=target.mention)
            embed.add_field(name="Discord ID", value=target.id)
            if user.get('verified_at'):
                embed.add_field(name="Verified At", value=user['verified_at'])
            await msg.edit(content=None, embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Not Verified",
                description="Please complete the verification form to gain access.",
                color=discord.Color.red()
            )
            await msg.edit(content=None, embed=embed)

    @commands.command(name='verifycheck')
    @commands.has_permissions(administrator=True)
    async def verifycheck_command(self, ctx):
        """Manual Google Sheets sync"""
        msg = await ctx.send("🔄 Syncing verification data from Google Sheets...")
        try:
            stats = await process_sheet_for_guild(ctx.guild.id, ctx.guild)
            embed = discord.Embed(title="🔄 Verification Sync Complete", color=discord.Color.blue())
            embed.add_field(name="Rows Checked", value=stats.get('rows_checked', 0))
            embed.add_field(name="New Submissions", value=stats.get('new_submissions', 0))
            embed.add_field(name="Verified Users", value=stats.get('verified_users', 0))
            embed.add_field(name="Invalid Submissions", value=stats.get('invalid_submissions', 0))
            embed.add_field(name="Duplicates", value=stats.get('duplicates', 0))
            embed.add_field(name="Errors", value=stats.get('errors', 0))
            await msg.edit(content=None, embed=embed)
        except Exception as e:
            await msg.edit(content=f"❌ Error during sync: {e}")

    @commands.command(name='unverify')
    @commands.has_permissions(administrator=True)
    async def unverify_command(self, ctx, member: discord.Member):
        """Unverify a user"""
        user = unverify_user(ctx.guild.id, member.id)
        if user:
            await ctx.send(f"✅ Successfully unverified {member.mention}.")
            create_log_entry(ctx.guild.id, 'User Unverified', member.id, staff_id=ctx.author.id)
        else:
            await ctx.send(f"⚠️ {member.mention} is not verified.")

    @commands.command(name='checkuser')
    @commands.has_permissions(administrator=True)
    async def checkuser_command(self, ctx, member: discord.Member):
        """Check detailed user info"""
        user = get_user_by_discord_id(ctx.guild.id, member.id)
        if not user:
            await ctx.send(f"❌ No records found for {member.mention}.")
            return

        embed = discord.Embed(title=f"User Info: {member.name}", color=discord.Color.blue())
        embed.add_field(name="Verified", value="✅ Yes" if getattr(user, 'is_verified', False) else "❌ No")
        
        if hasattr(user, 'codes'):
            embed.add_field(name="Codes Generated", value=len(user.codes))
        if hasattr(user, 'tickets'):
            open_tickets = [t for t in user.tickets if getattr(t, 'status', 'open') == 'open']
            embed.add_field(name="Active Tickets", value=len(open_tickets))
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
