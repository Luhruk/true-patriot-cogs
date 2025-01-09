import asyncio
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

        # Debug: Check total reactions
        total_reactions = sum(react.count for react in message.reactions)
        print(f"Message ID: {message.id}, Total Reactions: {total_reactions}")

        # Check if the message has 3 or more reactions
        if total_reactions >= 3:
            unique_reactors = set()
            for react in message.reactions:
                async for reactor in react.users():
                    unique_reactors.add(reactor.id)
                # Add a small delay to avoid hitting rate limits
                await asyncio.sleep(0.2)  # Adjust this value as needed

            # Debug: Check unique reactors
            print(f"Unique Reactors: {len(unique_reactors)}")

            # Ensure there are 3 unique reactors
            if len(unique_reactors) >= 3:
                embed = discord.Embed(
                    description=message.content,
                    color=discord.Color.blue(),
                    timestamp=message.created_at
                )
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
                embed.add_field(name="Original Message", value=f"[Jump to message]({message.jump_url})")
                await target_channel.send(embed=embed)
            else:
                print(f"Not enough unique reactors. Skipping.")
        else:
            print(f"Not enough reactions. Skipping.")
