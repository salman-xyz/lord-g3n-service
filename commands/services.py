import discord
from discord.ext import commands

from database import get_session
from database import Service, Code

class ServicesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='addservice')
    @commands.has_permissions(administrator=True)
    async def addservice_command(self, ctx, category: str, service_name: str):
        """Add a service"""
        category = category.lower()
        service_name = service_name.lower()
        with get_session() as session:
            service = session.query(Service).filter_by(guild_id=ctx.guild.id, name=service_name).first()
            if service:
                await ctx.send(f"⚠️ Service `{service_name}` already exists in category `{service.category}`.")
                return
            
            new_service = Service(guild_id=ctx.guild.id, name=service_name, category=category, enabled=True)
            session.add(new_service)
            session.commit()
            await ctx.send(f"✅ Added service `{service_name}` to category `{category}`.")

    @commands.command(name='removeservice')
    @commands.has_permissions(administrator=True)
    async def removeservice_command(self, ctx, service_name: str):
        """Remove a service"""
        service_name = service_name.lower()
        with get_session() as session:
            service = session.query(Service).filter_by(guild_id=ctx.guild.id, name=service_name).first()
            if not service:
                await ctx.send(f"❌ Service `{service_name}` not found.")
                return
            
            session.delete(service)
            session.commit()
            await ctx.send(f"✅ Removed service `{service_name}`.")

    @commands.command(name='enable')
    @commands.has_permissions(administrator=True)
    async def enable_command(self, ctx, service_name: str):
        """Enable a service"""
        service_name = service_name.lower()
        with get_session() as session:
            service = session.query(Service).filter_by(guild_id=ctx.guild.id, name=service_name).first()
            if not service:
                await ctx.send(f"❌ Service `{service_name}` not found.")
                return
            
            service.enabled = True
            session.commit()
            await ctx.send(f"✅ Enabled service `{service_name}`.")

    @commands.command(name='disable')
    @commands.has_permissions(administrator=True)
    async def disable_command(self, ctx, service_name: str):
        """Disable a service"""
        service_name = service_name.lower()
        with get_session() as session:
            service = session.query(Service).filter_by(guild_id=ctx.guild.id, name=service_name).first()
            if not service:
                await ctx.send(f"❌ Service `{service_name}` not found.")
                return
            
            service.enabled = False
            session.commit()
            await ctx.send(f"✅ Disabled service `{service_name}`.")

    @commands.command(name='services')
    async def services_command(self, ctx):
        """List all services"""
        with get_session() as session:
            services = session.query(Service).filter_by(guild_id=ctx.guild.id).all()
            
        if not services:
            await ctx.send("❌ No services configured.")
            return

        categories = {}
        for s in services:
            cap_category = s.category.capitalize()
            if cap_category not in categories:
                categories[cap_category] = []
            categories[cap_category].append(s)

        desc = "📋 Available Services\n\n"
        for category, svcs in categories.items():
            desc += f"**{category}**\n"
            for i, s in enumerate(svcs):
                is_last = (i == len(svcs) - 1)
                prefix = "└──" if is_last else "├──"
                status = "✅" if s.enabled else "❌"
                desc += f"{prefix} {s.name.capitalize()} {status}\n"
            desc += "\n"

        embed = discord.Embed(description=desc, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command(name='stock')
    async def stock_command(self, ctx, service_name: str = None):
        """Show available stock. Usage: !stock [service]"""
        from services.configuration_service import ConfigurationService
        
        with get_session() as session:
            config_service = ConfigurationService(session, ctx.guild.id)
            
            # Query enabled services
            query = session.query(Service).filter(
                Service.guild_id == ctx.guild.id,
                Service.enabled == True
            )
            if service_name:
                query = query.filter(Service.name == service_name.lower())
            
            services = query.order_by(Service.category, Service.name).all()
            
            if not services:
                embed = discord.Embed(
                    title="Lord G3N Available Stock",
                    description="❌ No services are currently available.",
                    color=discord.Color.blue()
                )
                embed.set_footer(text="Lord G3N Stock System")
                await ctx.send(embed=embed)
                return
            
            # Group services by category
            services_by_category = {}
            for svc in services:
                cat = svc.category.capitalize()
                if cat not in services_by_category:
                    services_by_category[cat] = []
                
                # Count unused codes in stock for this service
                stock_count = session.query(Code).filter(
                    Code.guild_id == ctx.guild.id,
                    Code.service_id == svc.id,
                    Code.status == "unused"
                ).count()
                
                services_by_category[cat].append((svc.name, stock_count))
            
            # Build description
            desc_lines = []
            for category, svcs in services_by_category.items():
                desc_lines.append(f"**{category}**")
                for name, count in svcs:
                    desc_lines.append(f"• {name.capitalize()} `{count}`")
                desc_lines.append("")  # Blank line between categories
            
            description = "\n".join(desc_lines).strip()
            
            embed = discord.Embed(
                title="Lord G3N Available Stock",
                description=description,
                color=discord.Color.blue()
            )
            
            # Thumbnail: custom setting, guild icon, or bot avatar
            thumbnail_url = config_service.get_setting("stock_thumbnail_url")
            if not thumbnail_url and ctx.guild and ctx.guild.icon:
                thumbnail_url = ctx.guild.icon.url
            elif not thumbnail_url and ctx.bot.user:
                thumbnail_url = ctx.bot.user.display_avatar.url
                
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
                
            embed.set_footer(text="Lord G3N Stock System")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServicesCog(bot))
