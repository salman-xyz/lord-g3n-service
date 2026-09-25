import discord
from discord.ext import commands

from services.configuration_service import set_setting
from services.code_generator import get_code_by_value, invalidate_code, get_code_stats
from services.verification_service import get_user_stats
from services.ticket_service import get_ticket_stats
from services.logging_service import create_log_entry
from database import get_session
from database import Service

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='checkcode')
    @commands.has_permissions(administrator=True)
    async def checkcode_command(self, ctx, code_str: str):
        code = get_code_by_value(ctx.guild.id, code_str)
        if not code:
            await ctx.send(f"❌ Code `{code_str}` not found.")
            return
        
        embed = discord.Embed(title=f"Code: {code.code}", color=discord.Color.blue())
        embed.add_field(name="Service", value=getattr(code, 'service_name', 'Unknown'))
        embed.add_field(name="Category", value=getattr(code, 'category', 'Unknown'))
        embed.add_field(name="Status", value="Redeemed" if getattr(code, 'redeemed', False) else "Unused")
        await ctx.send(embed=embed)

    @commands.command(name='invalidatecode')
    @commands.has_permissions(administrator=True)
    async def invalidatecode_command(self, ctx, code_str: str):
        code = invalidate_code(ctx.guild.id, code_str)
        if not code:
            await ctx.send(f"❌ Code `{code_str}` not found or already invalid/redeemed.")
            return
        
        await ctx.send(f"✅ Code `{code_str}` invalidated successfully.")
        create_log_entry(ctx.guild.id, 'Code Invalidated', staff_id=ctx.author.id, details=f"Code: {code_str}")

    @commands.command(name='stats')
    @commands.has_permissions(administrator=True)
    async def stats_command(self, ctx):
        user_stats = get_user_stats(ctx.guild.id)
        code_stats = get_code_stats(ctx.guild.id)
        ticket_stats = get_ticket_stats(ctx.guild.id)
        
        with get_session() as session:
            services = session.query(Service).filter_by(guild_id=ctx.guild.id).all()
        
        embed = discord.Embed(title="📊 Lord G3N Services Statistics", color=discord.Color.gold())
        
        embed.add_field(name="Users", value=f"Total Users: {user_stats.get('total', 0)}\\nVerified Users: {user_stats.get('verified', 0)}", inline=False)
        embed.add_field(name="Codes", value=f"Generated: {code_stats.get('generated', 0)}\\nUnused: {code_stats.get('unused', 0)}\\nRedeemed: {code_stats.get('redeemed', 0)}\\nExpired: {code_stats.get('expired', 0)}", inline=False)
        embed.add_field(name="Tickets", value=f"Active: {ticket_stats.get('active', 0)}\\nClosed: {ticket_stats.get('closed', 0)}", inline=False)
        
        svc_text = ""
        for s in services:
            svc_text += f"{s.name.capitalize()}: {'✅' if getattr(s, 'enabled', False) else '❌'}\\n"
        
        if svc_text:
            embed.add_field(name="Services", value=svc_text, inline=False)
            
        await ctx.send(embed=embed)

    async def _set_and_confirm(self, ctx, key: str, value: str, display_name: str):
        set_setting(ctx.guild.id, key, value, updated_by=ctx.author.id)
        await ctx.send(f"✅ **{display_name}** has been set to: `{value}`")
        create_log_entry(ctx.guild.id, f'Setting Updated: {key}', staff_id=ctx.author.id, details=f"New value: {value}")

    @commands.command(name='setform')
    @commands.has_permissions(administrator=True)
    async def setform_command(self, ctx, url: str):
        await self._set_and_confirm(ctx, 'google_form_url', url, "Google Form URL")

    @commands.command(name='setads')
    @commands.has_permissions(administrator=True)
    async def setads_command(self, ctx, url: str):
        await self._set_and_confirm(ctx, 'ads_website_url', url, "Ads Website URL")

    @commands.command(name='setticketchannel')
    @commands.has_permissions(administrator=True)
    async def setticketchannel_command(self, ctx, channel: discord.TextChannel):
        await self._set_and_confirm(ctx, 'ticket_panel_channel', str(channel.id), "Ticket Panel Channel")

    @commands.command(name='setstaffrole')
    @commands.has_permissions(administrator=True)
    async def setstaffrole_command(self, ctx, role: discord.Role):
        await self._set_and_confirm(ctx, 'staff_role', str(role.id), "Staff Role")

    @commands.command(name='setredeemcategory')
    @commands.has_permissions(administrator=True)
    async def setredeemcategory_command(self, ctx, category: discord.CategoryChannel):
        await self._set_and_confirm(ctx, 'redeem_ticket_category', str(category.id), "Redeem Ticket Category")

    @commands.command(name='setrewardcategory')
    @commands.has_permissions(administrator=True)
    async def setrewardcategory_command(self, ctx, category: discord.CategoryChannel):
        await self._set_and_confirm(ctx, 'reward_ticket_category', str(category.id), "Reward Ticket Category")

    @commands.command(name='setsupportcategory')
    @commands.has_permissions(administrator=True)
    async def setsupportcategory_command(self, ctx, category: discord.CategoryChannel):
        await self._set_and_confirm(ctx, 'support_ticket_category', str(category.id), "Support Ticket Category")

    @commands.command(name='setlogchannel')
    @commands.has_permissions(administrator=True)
    async def setlogchannel_command(self, ctx, channel: discord.TextChannel):
        await self._set_and_confirm(ctx, 'ticket_log_channel', str(channel.id), "Log Channel")

    @commands.command(name='setmaxactive')
    @commands.has_permissions(administrator=True)
    async def setmaxactive_command(self, ctx, count: int):
        if count < 1:
            await ctx.send("❌ Must be at least 1")
            return
        await self._set_and_confirm(ctx, 'max_active_tickets', str(count), "Max Active Tickets")

    @commands.command(name='cleanstale')
    @commands.has_permissions(administrator=True)
    async def cleanstale_command(self, ctx, member: discord.Member = None):
        """Clean up tickets for deleted channels"""
        from database import get_db, Ticket
        db = next(get_db())
        try:
            query = db.query(Ticket).filter(
                Ticket.guild_id == ctx.guild.id,
                Ticket.status == "open"
            )
            if member:
                query = query.filter(Ticket.discord_id == member.id)
            
            tickets = query.all()
            cleaned = 0
            for ticket in tickets:
                channel = ctx.guild.get_channel(ticket.channel_id)
                if not channel:
                    ticket.status = "closed"
                    ticket.closed_at = __import__('datetime').datetime.utcnow()
                    ticket.deleted_by = ctx.author.id
                    ticket.delete_reason = "Channel deleted (cleanup)"
                    cleaned += 1
            
            if cleaned:
                db.commit()
            
            await ctx.send(f"✅ Cleaned up {cleaned} stale ticket(s) for {member.mention if member else 'all users'}.")
        finally:
            db.close()

    @commands.command(name='forceclose')
    @commands.has_permissions(administrator=True)
    async def forceclose_command(self, ctx, member: discord.Member):
        """Force close all open tickets for a user"""
        from database import get_db, Ticket
        from datetime import datetime
        db = next(get_db())
        try:
            tickets = db.query(Ticket).filter(
                Ticket.guild_id == ctx.guild.id,
                Ticket.discord_id == member.id,
                Ticket.status == "open"
            ).all()
            
            for ticket in tickets:
                ticket.status = "closed"
                ticket.closed_at = datetime.utcnow()
                ticket.deleted_by = ctx.author.id
                ticket.delete_reason = "Force closed by admin"
            
            if tickets:
                db.commit()
            
            await ctx.send(f"✅ Force closed {len(tickets)} ticket(s) for {member.mention}.")
        finally:
            db.close()

    @commands.command(name='setavatar')
    @commands.has_permissions(administrator=True)
    async def setavatar_command(self, ctx, url: str = None):
        """Set bot avatar/profile pic (supports animated GIF and Image). Usage: !setavatar <url> or attach file"""
        import aiohttp
        import re
        
        avatar_bytes = None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        }
        
        if ctx.message.attachments:
            avatar_bytes = await ctx.message.attachments[0].read()
        elif url:
            # Clean url
            url = url.strip("<>")
            
            async with aiohttp.ClientSession(headers=headers) as session:
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            content_type = resp.headers.get("Content-Type", "")
                            # If it's an HTML page (like imgur album or tenor page), try to find og:image or video
                            if "text/html" in content_type:
                                html_text = await resp.text()
                                # Find og:image or og:video
                                og_match = re.search(r'<meta\s+(?:property|name)=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
                                if not og_match:
                                    og_match = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']og:image["\']', html_text, re.IGNORECASE)
                                
                                if og_match:
                                    img_url = og_match.group(1)
                                    async with session.get(img_url) as img_resp:
                                        if img_resp.status == 200:
                                            avatar_bytes = await img_resp.read()
                                        else:
                                            await ctx.send(f"❌ Failed to download resolved image from `{img_url}` (Status {img_resp.status}).")
                                            return
                                else:
                                    await ctx.send("❌ Could not find direct image/GIF inside the provided link. Please upload the GIF file directly with `!setavatar`.")
                                    return
                            else:
                                avatar_bytes = await resp.read()
                        else:
                            await ctx.send(f"❌ Failed to download image from URL (Status {resp.status}).\n💡 **টিপ:** আপনি সরাসরি ডিসকর্ডে GIF ফাইলটি এটাচ (upload) করে `!setavatar` লিখুন।")
                            return
                except Exception as e:
                    await ctx.send(f"❌ Error downloading file: {e}")
                    return
        else:
            await ctx.send("❌ Please provide a GIF/image URL or attach a file with the command.\nUsage: `!setavatar <url>` or attach a GIF/Image with `!setavatar`")
            return
            
        try:
            await self.bot.user.edit(avatar=avatar_bytes)
            await ctx.send("✅ Bot profile picture/GIF updated successfully!")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to update avatar: {e}\n*(Note: Discord limits avatar changes to a few times per hour)*")

    @commands.command(name='setbotname')
    @commands.has_permissions(administrator=True)
    async def setbotname_command(self, ctx, *, new_name: str):
        """Set bot username. Usage: !setbotname <name>"""
        try:
            await self.bot.user.edit(username=new_name)
            await ctx.send(f"✅ Bot username changed to `{new_name}`.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to change username: {e}")

    @commands.command(name='setgenbanner', aliases=['setgengif', 'genbanner'])
    @commands.has_permissions(administrator=True)
    async def setgenbanner_command(self, ctx, url: str = None):
        """Set the banner/GIF for generator !gen embeds. Usage: !setgenbanner <url> or attach image/gif"""
        banner_url = None
        if ctx.message.attachments:
            banner_url = ctx.message.attachments[0].url
        elif url:
            banner_url = url.strip("<>")
        else:
            await ctx.send("❌ Please provide a banner URL or attach an image/GIF file.\nUsage: `!setgenbanner <url>` or attach an image/GIF with `!setgenbanner`")
            return
            
        set_setting(ctx.guild.id, 'gen_gif_url', banner_url, updated_by=ctx.author.id)
        embed = discord.Embed(
            title="✅ Generator Banner Updated",
            description=f"Generator banner has been updated successfully!\nURL: `{banner_url}`",
            color=discord.Color.green()
        )
        embed.set_image(url=banner_url)
        await ctx.send(embed=embed)
        create_log_entry(ctx.guild.id, 'Setting Updated: gen_gif_url', staff_id=ctx.author.id, details=f"New banner: {banner_url}")

    @commands.command(name='setticketbanner', aliases=['setticketgif', 'ticketbanner'])
    @commands.has_permissions(administrator=True)
    async def setticketbanner_command(self, ctx, url: str = None):
        """Set the banner/GIF for !ticketpanels embed. Usage: !setticketbanner <url> or attach image/gif"""
        banner_url = None
        if ctx.message.attachments:
            banner_url = ctx.message.attachments[0].url
        elif url:
            banner_url = url.strip("<>")
        else:
            await ctx.send("❌ Please provide a banner URL or attach an image/GIF file.\nUsage: `!setticketbanner <url>` or attach an image/GIF with `!setticketbanner`")
            return
            
        set_setting(ctx.guild.id, 'ticket_gif_url', banner_url, updated_by=ctx.author.id)
        embed = discord.Embed(
            title="✅ Ticket Panel Banner Updated",
            description=f"Ticket panel banner has been updated successfully!\nURL: `{banner_url}`\n*(Run `!ticketpanels` to view your updated ticket panel)*",
            color=discord.Color.green()
        )
        embed.set_image(url=banner_url)
        await ctx.send(embed=embed)
        create_log_entry(ctx.guild.id, 'Setting Updated: ticket_gif_url', staff_id=ctx.author.id, details=f"New banner: {banner_url}")

    @commands.command(name='setstockbanner', aliases=['setstockthumbnail'])
    @commands.has_permissions(administrator=True)
    async def setstockbanner_command(self, ctx, url: str = None):
        """Set the thumbnail/banner for !stock command. Usage: !setstockbanner <url> or attach image/gif"""
        banner_url = None
        if ctx.message.attachments:
            banner_url = ctx.message.attachments[0].url
        elif url:
            banner_url = url.strip("<>")
        else:
            await ctx.send("❌ Please provide an image/GIF URL or attach a file.\nUsage: `!setstockbanner <url>`")
            return
            
        set_setting(ctx.guild.id, 'stock_thumbnail_url', banner_url, updated_by=ctx.author.id)
        embed = discord.Embed(
            title="✅ Stock Thumbnail Updated",
            description=f"Stock thumbnail has been updated successfully!\nURL: `{banner_url}`",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=banner_url)
        await ctx.send(embed=embed)
        create_log_entry(ctx.guild.id, 'Setting Updated: stock_thumbnail_url', staff_id=ctx.author.id, details=f"New thumbnail: {banner_url}")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))

