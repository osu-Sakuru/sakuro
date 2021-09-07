# -*- coding: utf-8 -*-

from datetime import datetime
from random import choice
from typing import Union

import DiscordUtils
from cmyui import log, Ansi
from cmyui.osu import Mods
from discord import Embed
from discord.ext import commands

from objects.sakuro import Sakuro, ContextWrap
from osu.calculator import Calculator
from objects import config
from utils.misc import convert_mode_int, convert_grade_emoji, get_completion, get_level, get_level_percent, sakuro_error
from objects.user import UserHelper
from utils.wrappers import check_args, link_required, sakuroCommand


class OsuCog(commands.Cog, name='Osu'):
    """Main bot commands."""

    def __init__(self, bot: Sakuro):
        self.bot = bot

    @sakuroCommand(
        brief="Shows your/users stats on Sakuru.",
        help="Shows your/users stats on Sakuru, you also can use positional arguments for different modes i.e\n" +
             f"{config.PREFIX}osu alowave -rx -mania",
        usage=f"{config.PREFIX}osu [username] [vn/rx/ap] [std/taiko/mania]"
    )
    @link_required
    @check_args
    async def osu(self, ctx: ContextWrap, player: Union[dict, str] = None, mods: str = 'vn',
                  mode: str = 'std'):
        scope = await UserHelper.getOsuUserByName(player['safe_name'], scope="all")
        stats = scope['stats'][f'{mods}_{mode}']

        level = get_level(stats['tscore'])
        level_percent = get_level_percent(stats['tscore'], level)

        # Donors ♥️
        # NOTE: 48 Premium & Supporter
        isDonor = scope['info']['priv'] & 48

        embed = Embed(description=f"**▸ Official Rank:** #{stats['rank']} " +
                                  f"({scope['info']['country'].upper()}#{stats['crank']})\n**▸ " +
                                  f"Level:** {level} ({level_percent:.2f}%)\n**▸ Total PP:** {stats['pp']}\n**▸ " +
                                  f"Hit Accuracy:** {stats['acc']:.2f}%\n**▸ " +
                                  f"Playcount:** {stats['plays']}" +
                                  f'\n\n**▸ {player["name"]} is a Supporter:** ♥️' if isDonor else '',
                      timestamp=datetime.now(), colour=0x00ff00)

        embed.set_author(name=f"{mode.upper()}!{mods.upper()} Profile for {player['name']}",
                         icon_url=f"https://sakuru.pw/static/flags/{scope['info']['country'].upper()}.png",
                         url=f"https://sakuru.pw/u/{scope['info']['id']}")

        embed.set_thumbnail(url=f"https://a.sakuru.pw/{scope['info']['id']}")
        embed.set_footer(text="On Sakuru.pw server.")

        await ctx.send(embed=embed)

    @sakuroCommand(
        aliases=['rs'],
        brief="Shows your recent score.",
        help="Shows your recent posted score on Sakuru, also you can pass argument for " +
             f"relax or other modes by `{config.PREFIX}recent -rx`",
        usage=f"`{config.PREFIX}recent [username] [vn/rx/ap] [std/taiko/mania]`"
    )
    @link_required
    @check_args
    async def recent(self, ctx: ContextWrap, player: Union[dict, str] = None, mods: str = 'vn',
                     mode: str = 'std') -> None:
        score = (await UserHelper.getUserScores(player['safe_name'], convert_mode_int(mode), mods, 1, 'recent'))[0]
        self.bot.cache['latest_maps'][ctx.channel.id] = score['beatmap']['id']

        calc = await Calculator.calculate(
            score['beatmap']['id'],
            convert_mode_int(mode),
            score['mods'],
            score['acc'],
            None
        )

        choke_str = f'*({calc["pp"]:.2f}PP for {score["acc"]:.2f}% FC)*' \
            if score['grade'] not in ('S', 'SS', 'X', 'SH') else ''
        completion_str = f"\n▸ Map Completion: {get_completion(score['time_elapsed'], score['beatmap']['total_length'])}%" \
            if score['grade'] == 'F' else ''

        embed = Embed(description=f"▸ {convert_grade_emoji(score['grade'])} ▸ **{score['pp']:.2f}PP** {choke_str}" \
                                  f"▸ {score['acc']:.2f}%\n▸ {score['score']} ▸ x{score['max_combo']}/{score['beatmap']['max_combo']} " \
                                  f"▸ [{score['n300']}/{score['n100']}/{score['n50']}/{score['nmiss']}]{completion_str}" \
                                  f"\n▸ Score Set <t:{datetime.fromisoformat(score['play_time']).timestamp().__int__()}:R>",
                      timestamp=datetime.fromisoformat(score['play_time']), colour=ctx.author.color)

        mods_str = f' +{Mods(score["mods"])!r} ' \
            if score['mods'] != 0 else ' '
        embed.set_author(
            name=calc['map_fullname'] + mods_str + f"[{calc['stars']:.2f}★]",
            url=f"https://chimu.moe/d/{score['beatmap']['set_id']}",
            icon_url=f"https://a.sakuru.pw/{player['id']}")

        embed.set_thumbnail(url=f"https://b.ppy.sh/thumb/{score['beatmap']['set_id']}l.jpg")
        embed.set_footer(text=f"Played on Sakuru.pw server. | Map By {calc['map_creator']}")

        await ctx.send(embed=embed)

    @sakuroCommand(
        aliases=['top', 'best'],
        brief="Shows your best scores.",
        help="Shows your best scores on Sakuru, also you can pass argument for " +
             f"relax or other modes by `{config.PREFIX}topscores -rx`",
        usage=f"`{config.PREFIX}topscores [username] [vn/rx/ap] [std/taiko/mania]`"
    )
    @link_required
    @check_args
    async def topscores(self, ctx: ContextWrap, player: Union[dict, str] = None, mods: str = 'vn',
                        mode: str = 'std') -> None:
        scores = await UserHelper.getUserScores(player['safe_name'], convert_mode_int(mode), mods, 100, 'best')

        if len(scores) == 0:
            await ctx.send(embed=sakuro_error(
                title="Something went wrong!",
                error=f"`{player['name']}` have no scores on `{mods.upper()}!{mode.upper()}`",
                color=ctx.author.color
            ))
            return

        paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, remove_reactions=True, timeout=120)

        paginator.add_reaction('⏮️', "first")
        paginator.add_reaction('⏪', "back")
        paginator.add_reaction('🔐', "lock")
        paginator.add_reaction('⏩', "next")
        paginator.add_reaction('⏭️', "last")

        embeds = []
        description = ""

        for idx, score in enumerate(scores):
            calc = await Calculator.calculate(
                score['beatmap']['id'],
                convert_mode_int(mode),
                score['mods'],
                score['acc'],
                None
            )

            choke_str = f'*({calc["pp"]:.2f}PP for {score["acc"]:.2f}% FC)*' \
                if score['grade'] not in ('S', 'SS', 'X', 'SH') else ''
            mods_str = f' +{Mods(score["mods"])!r}' \
                if score['mods'] != 0 else ''

            description += f"""** {idx + 1}. [{calc['map_fullname']}](https://skuru.pw/direct?id={score['beatmap']['id']})""" \
                           f"{mods_str}** [{calc['stars']:.2f}★]\n" \
                           f"▸ {convert_grade_emoji(score['grade'])} ▸ **{score['pp']:.2f}PP** {choke_str}" \
                           f"▸ {score['acc']:.2f}%\n▸ {score['score']} ▸ x{score['max_combo']}/{score['beatmap']['max_combo']} " \
                           f"▸ [{score['n300']}/{score['n100']}/{score['n50']}/{score['nmiss']}]\n" \
                           f"▸ Score Set <t:{datetime.fromisoformat(score['play_time']).timestamp().__int__()}:R>\n"

            if len(scores) < 5:
                if idx % len(scores) == len(scores) - 1:
                    embed = Embed(color=ctx.author.color, description=description)

                    embed.set_author(name=f"Top {len(scores)} {mode.upper()}!{mods.upper()} Plays for {player['name']}",
                                     url=f"https://sakuru.pw/u/{player['id']}",
                                     icon_url=f"https://sakuru.pw/static/flags/{player['country'].upper()}.png")
                    embed.set_footer(text="On Sakuru.pw server.",
                                     icon_url="https://sakuru.pw/static/ingame.png")
                    embed.set_thumbnail(url=f"https://a.sakuru.pw/{player['id']}")

                    await ctx.send(embed=embed)
                    return
            elif idx % 5 == 4:
                embed = Embed(color=ctx.author.color, description=description)
                description = ""

                embed.set_author(name=f"Top {len(scores)} {mode.upper()}!{mods.upper()} Plays for {player['name']}",
                                 url=f"https://sakuru.pw/u/{player['id']}",
                                 icon_url=f"https://sakuru.pw/static/flags/{player['country'].upper()}.png")
                embed.set_footer(text="On Sakuru.pw server.",
                                 icon_url="https://sakuru.pw/static/ingame.png")
                embed.set_thumbnail(url=f"https://a.sakuru.pw/{player['id']}")

                embeds.append(embed)

        await paginator.run(embeds)

    @sakuroCommand(
        aliases=['cur', 'c'],
        brief="Shows your best scores on current beatmap.",
        help="Shows your best scores on current beatmap, also you can pass argument for " +
             f"relax or other modes by `{config.PREFIX}current -rx`",
        usage=f"`{config.PREFIX}current [username] [vn/rx/ap] [std/taiko/mania]`"
    )
    @link_required
    @check_args
    async def current(self, ctx: ContextWrap, player: Union[dict, str] = None, mods: str = 'vn',
                        mode: str = 'std') -> None:
        if not self.bot.cache['latest_maps'].get(ctx.channel.id):
            await ctx.send(embed=sakuro_error(
                title="Something went wrong!",
                error=f"Not found latest beatmap in this channel.",
                color=ctx.author.color
            ))
            return

        scores = await UserHelper.getUserScores(player['id'], convert_mode_int(mode), mods, 5, 'best',
                                                self.bot.cache['latest_maps'].get(ctx.channel.id))

        if len(scores) == 0:
            await ctx.send(embed=sakuro_error(
                title="Something went wrong!",
                error=f"`{player['name']}` have no scores on this beatmap.",
                color=ctx.author.color
            ))
            return

        map_fullname = ""
        description = ""

        for idx, score in enumerate(scores):
            calc = await Calculator.calculate(
                score['beatmap']['id'],
                convert_mode_int(mode),
                score['mods'],
                score['acc'],
                None
            )
            map_fullname = calc['map_fullname']

            choke_str = f'*({calc["pp"]:.2f}PP for {score["acc"]:.2f}% FC)*' \
                if score['grade'] not in ('S', 'SS', 'X', 'SH') else ''
            mods_str = f' +{Mods(score["mods"])!r}' \
                if score['mods'] != 0 else ''

            description += f"""** {idx + 1}. {mods_str}** [{calc['stars']:.2f}★]\n""" \
                           f"▸ {convert_grade_emoji(score['grade'])} ▸ **{score['pp']:.2f}PP** {choke_str}" \
                           f"▸ {score['acc']:.2f}%\n▸ {score['score']} ▸ x{score['max_combo']}/{score['beatmap']['max_combo']} " \
                           f"▸ [{score['n300']}/{score['n100']}/{score['n50']}/{score['nmiss']}]\n" \
                           f"▸ Score Set <t:{datetime.fromisoformat(score['play_time']).timestamp().__int__()}:R>\n"

        embed = Embed(color=ctx.author.color, description=description)

        embed.set_author(name=f"Top {len(scores)} Plays for {player['name']} on {map_fullname}",
                         url=f"https://sakuru.pw/u/{player['id']}",
                         icon_url=f"https://sakuru.pw/static/flags/{player['country'].upper()}.png")
        embed.set_footer(text="On Sakuru.pw server.",
                         icon_url="https://sakuru.pw/static/ingame.png")
        embed.set_thumbnail(url=f"https://a.sakuru.pw/{player['id']}")

        await ctx.send(embed=embed)

def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(OsuCog(bot))
