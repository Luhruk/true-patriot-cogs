from .reaction_reposter import ReactionReposter

async def setup(bot):
    await bot.add_cog(ReactionReposter(bot))
