# -*- coding: utf-8 -*-

from cmyui import log, Ansi
from discord.ext import commands
from discord.ext.commands import Bot, Context


class AdminCog(commands.Cog, name='Admin'):
    """Utilities for bot owner."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx: Context, module: str):
        """Reloads a module."""
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send('\N{PISTOL}')
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('\N{OK HAND SIGN}')

def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(AdminCog(bot))
