import asyncio
from redbot.core import commands, Config
import discord

class ReactionReposter(commands.Cog):
    """A cog to repost messages with a configurable number of reactions to a different channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(target_channel=None, reaction_threshold=3)  # Default threshold is 3
        self.reposted_messages = set()  # Set to keep track of reposted messages

    @commands.group()
    @commands.guild_only()
    @commands.admin()
    async def reposterset(self, ctx):
        """Configuration commands for Reaction Reposter."""
        if ctx.invoked_subcommand is None:
            # Only send help if no subcommand was invoked
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

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return  # Ignore bot reactions

        message = reaction.message
        guild = message.guild

        # Debug: Check if this is in a guild
        if not guild:
            print(f"Not in a guild. Skipping.")
            return

        # Debug: Check if a target channel is set
        target_channel_id = await self.config.guild(guild).target_channel()
        if not target_channel_id:
            print(f"No target channel set for {guild.name}. Skipping.")
            return

        target_channel = guild.get_channel(target_channel_id)
        if not target_channel:
            print(f"Invalid target channel for {guild.name}. Skipping.")
            return

        # Check if the message has already been reposted
        if message.id in self.reposted_messages:
            print(f"Message {message.id} already reposted. Skipping.")
            return

        # Get the reaction threshold for this guild
        threshold = await self.config.guild(guild).reaction_threshold()
        print(f"Reaction threshold for {guild.name}: {threshold}")

        # Debug: Check total reactions
        total_reactions = sum(react.count for react in message.reactions)
        print(f"Message ID: {message.id}, Total Reactions: {total_reactions}")

        # Check if the message has enough reactions
        if total_reactions >= threshold:
            unique_reactors = set()
            for react in message.reactions:
                # Instead of fetching users for each reaction, we check if there are enough unique reactors
                async for reactor in react.users():
                    unique_reactors.add(reactor.id)
                # Add a small delay to avoid hitting rate limits
                await asyncio.sleep(0.2)  # Adjust this value as needed

            # Debug: Check unique reactors
            print(f"Unique Reactors: {len(unique_reactors)}")

            # Ensure there are enough unique reactors
            if len(unique_reactors) >= threshold:
                embed = discord.Embed(
                    description=message.content,
                    color=discord.Color.blue(),
                    timestamp=message.created_at
                )
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
                embed.add_field(name="Original Message", value=f"[Jump to message]({message.jump_url})")

                # Add attachments if any
                for attachment in message.attachments:
                    if attachment.height:  # Image or video
                        embed.set_image(url=attachment.url)  # Set the first image/video as the embed image
                    else:
                        # If it's a file, send it as an attachment
                        await target_channel.send(file=discord.File(attachment.url, filename=attachment.filename))

                await target_channel.send(embed=embed)

                # Mark the message as reposted
                self.reposted_messages.add(message.id)
            else:
                print(f"Not enough unique reactors. Skipping.")
        else:
            print(f"Not enough reactions. Skipping.")
