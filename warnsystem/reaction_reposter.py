from redbot.core import commands, Config
import discord

class ReactionReposter(commands.Cog):
    """A cog to repost messages with 3 or more reactions to a different channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(target_channel=None)

    @commands.group()
    @commands.guild_only()
    @commands.admin()
    async def reposterset(self, ctx):
        """Configuration commands for Reaction Reposter."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @reposterset.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where messages will be reposted."""
        await self.config.guild(ctx.guild).target_channel.set(channel.id)
        await ctx.send(f"Repost channel set to {channel.mention}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return  # Ignore bot reactions

        message = reaction.message
        guild = message.guild

        # Ensure this is in a guild and a repost channel is set
        if not guild:
            return

        target_channel_id = await self.config.guild(guild).target_channel()
        if not target_channel_id:
            return

        target_channel = guild.get_channel(target_channel_id)
        if not target_channel:
            return

        # Check if the message has 3 or more unique reactions
        if len(reaction.message.reactions) >= 3:
            unique_reactors = set()
            for react in reaction.message.reactions:
                async for reactor in react.users():
                    unique_reactors.add(reactor.id)

            if len(unique_reactors) >= 3:
                embed = discord.Embed(
                    description=message.content,
                    color=discord.Color.blue(),
                    timestamp=message.created_at
                )
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
                embed.add_field(name="Original Message", value=f"[Jump to message]({message.jump_url})")
                await target_channel.send(embed=embed)
