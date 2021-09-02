# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Union

from cmyui import log, Ansi
from cmyui.osu import Mods
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Context

from osu.calculator import Calculator
from utils.misc import convert_mode_int, convert_grade_emoji, get_completion
from utils.user import UserHelper
from utils.wrappers import handle_exception, link_required, check_args


class RecentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['rs'])
    @handle_exception
    @check_args
    @link_required
    async def recent(self, ctx: Context, player: Union[dict, str] = None, mods: str = 'vn', mode: str = 'std'):
        score = (await UserHelper.getUserScores(player['name'], convert_mode_int(mode), mods, 1, 'recent'))[0]
        calc = await Calculator.calculate(score['beatmap']['id'], convert_mode_int(mode), score['mods'], score['acc'], None)

        embed = Embed(description=f"""▸ {convert_grade_emoji(score['grade'])} ▸ **{score['pp']:.2f}PP**{f' *({calc["pp"]:.2f}PP for {score["acc"]:.2f}% FC)*' if score['grade'] not in ('S', 'SS', 'X', 'SH') else ''} """ +
                                  f"▸ {score['acc']:.2f}%\n▸ {score['score']} ▸ x{score['max_combo']}/{score['beatmap']['max_combo']} " +
                                  f"▸ [{score['n300']}/{score['n100']}/{score['n50']}/{score['nmiss']}]" +
                                  f"""{f"{chr(10)}▸ Map Completion: {get_completion(score['time_elapsed'], score['beatmap']['total_length'])}%" if score['grade'] == 'F' else ''}""" +
                                  f"\n▸ Score Set <t:{datetime.fromisoformat(score['play_time']).timestamp().__int__()}:R>",
                                  timestamp=datetime.fromisoformat(score['play_time']), colour=ctx.author.color)

        embed.set_author(name=f"""{calc['map_fullname']}{f' +{Mods(score["mods"])!r}' if score['mods'] != 0 else ''} [{calc['stars']:.2f}★]""",
                         url=f"https://chimu.moe/d/{score['beatmap']['set_id']}",
                         icon_url=f"https://a.sakuru.pw/{player['id']}")

        embed.set_thumbnail(url=f"https://b.ppy.sh/thumb/{score['beatmap']['set_id']}l.jpg")
        embed.set_footer(text=f"Played on Sakuru.pw server. | Map By {calc['map_creator']}")

        await ctx.send(embed=embed)

def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(RecentCog(bot))
