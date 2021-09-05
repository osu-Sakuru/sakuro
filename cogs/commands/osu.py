# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Union

import discord.utils
from cmyui import log, Ansi
from cmyui.osu import Mods
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context

from osu.calculator import Calculator
from utils import config, glob
from utils.misc import convert_mode_int, convert_grade_emoji, get_completion, get_level, get_level_percent
from utils.user import UserHelper
from utils.wrappers import handle_exception, check_args, link_required


class OsuCog(commands.Cog, name='Osu'):
    """Main bot commands."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        brief="Shows your/users stats on Sakuru.",
        help="Shows your/users stats on Sakuru, you also can use positional arguments for different modes i.e\n" +
             f"{config.PREFIX}osu alowave -rx -mania",
        usage=f"{config.PREFIX}osu [username] [vn/rx/ap] [std/taiko/mania]"
    )
    @handle_exception
    @link_required
    @check_args
    async def osu(self, ctx: Context, player: Union[dict, str] = None, mods: str = 'vn', mode: str = 'std'):
        scope = await UserHelper.getOsuUserByName(player['safe_name'], scope="all")
        stats = scope['stats'][f'{mods}_{mode}']

        level = get_level(stats['tscore'])
        level_percent = get_level_percent(stats['tscore'], level)

        # Donors ♥️
        isDonor = scope['info']['priv'] & 48

        embed = Embed(description=f"**▸ Official Rank:** #{stats['rank']} " +
                                  f"({scope['info']['country'].upper()}#{stats['crank']})\n**▸ " +
                                  f"Level:** {level} ({level_percent:.2f}%)\n**▸ Total PP:** {stats['pp']}\n**▸ " +
                                  f"Hit Accuracy:** {stats['acc']:.2f}%\n**▸ " +
                                  f"Playcount:** {stats['plays']}" +
                                  f"""{f'{chr(10) * 2}**▸ {player["name"]} is a Supporter:** ♥️' if isDonor else ''}""",
                      timestamp=datetime.now(), colour=0x00ff00)

        embed.set_author(name=f"{mode.upper()}!{mods.upper()} Profile for {player['name']}",
                         icon_url=f"https://sakuru.pw/static/flags/{scope['info']['country'].upper()}.png",
                         url=f"https://sakuru.pw/u/{scope['info']['id']}")

        embed.set_thumbnail(url=f"https://a.sakuru.pw/{scope['info']['id']}")
        embed.set_footer(text="On Sakuru.pw server.")

        await ctx.send(embed=embed)

    @commands.command(
        aliases=['rs'],
        brief="Shows your recent score.",
        help="Shows your recent posted score on Sakuru, also you can pass argument for " +
             f"relax or other modes by `{config.PREFIX}recent -rx`",
        usage=f"`{config.PREFIX}recent [username] [vn/rx/ap] [std/taiko/mania]`"
    )
    @handle_exception
    @link_required
    @check_args
    async def recent(self, ctx: Context, player: Union[dict, str] = None, mods: str = 'vn', mode: str = 'std'):
        score = (await UserHelper.getUserScores(player['safe_name'], convert_mode_int(mode), mods, 1, 'recent'))[0]
        calc = await Calculator.calculate(score['beatmap']['id'], convert_mode_int(mode), score['mods'], score['acc'],
                                          None)

        embed = Embed(description=f"▸ {convert_grade_emoji(score['grade'])} ▸ **{score['pp']:.2f}PP**" +
                                  f"""{f' *({calc["pp"]:.2f}PP for {score["acc"]:.2f}% FC)*' if score['grade'] not in ('S', 'SS', 'X', 'SH') else ''} """ +
                                  f"▸ {score['acc']:.2f}%\n▸ {score['score']} ▸ x{score['max_combo']}/{score['beatmap']['max_combo']} " +
                                  f"▸ [{score['n300']}/{score['n100']}/{score['n50']}/{score['nmiss']}]" +
                                  f"""{f"{chr(10)}▸ Map Completion: {get_completion(score['time_elapsed'], score['beatmap']['total_length'])}%" if score['grade'] == 'F' else ''}""" +
                                  f"\n▸ Score Set <t:{datetime.fromisoformat(score['play_time']).timestamp().__int__()}:R>",
                      timestamp=datetime.fromisoformat(score['play_time']), colour=ctx.author.color)

        embed.set_author(
            name=f"""{calc['map_fullname']}{f' +{Mods(score["mods"])!r}' if score['mods'] != 0 else ''} [{calc['stars']:.2f}★]""",
            url=f"https://chimu.moe/d/{score['beatmap']['set_id']}",
            icon_url=f"https://a.sakuru.pw/{player['id']}")

        embed.set_thumbnail(url=f"https://b.ppy.sh/thumb/{score['beatmap']['set_id']}l.jpg")
        embed.set_footer(text=f"Played on Sakuru.pw server. | Map By {calc['map_creator']}")

        await ctx.send(embed=embed)


def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(OsuCog(bot))