# -*- coding: utf-8 -*-
import inspect

from cmyui import log, Ansi
from discord.ext import commands
from discord.ext.commands import Bot


class MiscCog(commands.Cog, name='Misc'):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        help="Test!",
        brief="Wow!",
        usage="<that> (those) [this]"
    )
    async def test(self, ctx):
        print(self.bot.get_command('test').usage)
        await ctx.send("**Test**")

def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(MiscCog(bot))
