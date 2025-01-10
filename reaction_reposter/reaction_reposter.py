import asyncio
from redbot.core import commands, Config
import discord

class ReactionReposter(commands.Cog):
    """A cog to repost messages with a configurable number of reactions to a different channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(
            target_channel=None,
            reaction_threshold=3,
            excluded_channels=[],
            ignore_bot_messages=True,  # Default to ignoring bot messages
        )
        self.reposted_messages = set()  # Set to keep track of reposted messages

    @commands.group()
    @commands.guild_only()
    @commands.admin()
    async def reposterset(self, ctx):
        """Configuration commands for Reaction Reposter."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.reposterset)

    @reposterset.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where messages will be reposted."""
        await self.config.guild(ctx.guild).target_channel.set(channel.id)
        await ctx.send(f"Repost channel set to {channel.mention}")

    @reposterset.command()
    async def setthreshold(self, ctx, threshold: int):
        """Set the number of reactions required to repost a message."""
        if threshold < 1:
            await ctx.send("Threshold must be at least 1.")
            return
        await self.config.guild(ctx.guild).reaction_threshold.set(threshold)
        await ctx.send(f"Repost threshold set to {threshold} reactions.")

    @reposterset.command()
    async def excludechannel(self, ctx, channel: discord.TextChannel):
        """Exclude a channel from being reposted."""
        async with self.config.guild(ctx.guild).excluded_channels() as excluded:
            if channel.id not in excluded:
                excluded.append(channel.id)
                await ctx.send(f"{channel.mention} has been excluded from reposting.")
            else:
                await ctx.send(f"{channel.mention} is already excluded.")

    @reposterset.command()
    async def includechannel(self, ctx, channel: discord.TextChannel):
        """Include a previously excluded channel for reposting."""
        async with self.config.guild(ctx.guild).excluded_channels() as excluded:
            if channel.id in excluded:
                excluded.remove(channel.id)
                await ctx.send(f"{channel.mention} has been included for reposting.")
            else:
                await ctx.send(f"{channel.mention} is not excluded.")

    @reposterset.command()
    async def ignorebot(self, ctx, toggle: bool):
        """Set whether to ignore messages created by the bot."""
        await self.config.guild(ctx.guild).ignore_bot_messages.set(toggle)
        status = "ignoring" if toggle else "not ignoring"
        await ctx.send(f"The bot is now {status} messages created by itself.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return  # Ignore bot reactions

        message = reaction.message
        guild = message.guild

        if not guild:
            return

        # Check if ignoring bot messages
        ignore_bot_messages = await self.config.guild(guild).ignore_bot_messages()
        if ignore_bot_messages and message.author.bot:
            return

        target_channel_id = await self.config.guild(guild).target_channel()
        if not target_channel_id:
            return

        target_channel = guild.get_channel(target_channel_id)
        if not target_channel:
            return

        # Check if the channel is excluded
        excluded_channels = await self.config.guild(guild).excluded_channels()
        if message.channel.id in excluded_channels:
            return

        # Check if the message has already been reposted
        if message.id in self.reposted_messages:
            return

        # Get the reaction threshold for this guild
        threshold = await self.config.guild(guild).reaction_threshold()

        # Check total reactions
        total_reactions = sum(react.count for react in message.reactions)

        if total_reactions >= threshold:
            unique_reactors = set()
            for react in message.reactions:
                async for reactor in react.users():
                    unique_reactors.add(reactor.id)
                await asyncio.sleep(0.2)

            if len(unique_reactors) >= threshold:
                embed = discord.Embed(
                    description=message.content,
                    color=discord.Color.blue(),
                    timestamp=message.created_at,
                )
                embed.set_author(
                    name=message.author.display_name,
                    icon_url=message.author.avatar.url,
                )
                embed.add_field(
                    name="Original Message", value=f"[Jump to message]({message.jump_url})"
                )

                for attachment in message.attachments:
                    if attachment.height:  # Image or video
                        embed.set_image(url=attachment.url)
                    else:
                        await target_channel.send(
                            file=discord.File(
                                attachment.url, filename=attachment.filename
                            )
                        )

                await target_channel.send(embed=embed)
                self.reposted_messages.add(message.id)
