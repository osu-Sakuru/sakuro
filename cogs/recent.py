# -*- coding: utf-8 -*-
from datetime import datetime

from cmyui import log, Ansi
from discord import Embed
from discord.ext import commands

from osu.calculator import Calculator
from utils.misc import convert_mode_int
from utils.user import UserHelper
from utils.wrappers import handle_exception, link_required, check_args


class RecentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['rs'])
    @handle_exception
    @link_required
    @check_args
    async def recent(self, ctx, name: str = None, mods: str = 'vn', mode: str = 'std'):
        score = (await UserHelper.getUserScores(name, convert_mode_int(mode), mods, 1, 'recent'))[0]
        calc = await Calculator.calculate(score['beatmap']['id'], convert_mode_int(mode), score['mods'], score['acc'], None, score['nmiss'])

        map_id, pp, stars, map_creator, map_fullname = calc.as_dict

        print(map_id, pp, stars, map_creator, map_fullname)

        embed = Embed(description=f"a" +
                                  f"a" +
                                  f"a" +
                                  f"a", timestamp=datetime.now(), colour=0x00ff00)

        embed.set_footer(text="Played on Sakuru.pw server.")

        await ctx.send(embed=embed)

def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(RecentCog(bot))
