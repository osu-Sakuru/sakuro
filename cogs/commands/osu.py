# -*- coding: utf-8 -*-
import copy
from datetime import datetime

import discord
import DiscordUtils
from cmyui import Ansi
from cmyui import log
from cmyui.osu import Mods
from discord import Embed
from discord.ext import commands

from objects import config
from objects import glob
from objects.sakuro import ContextWrap
from objects.sakuro import Sakuro
from objects.user import UserHelper
from utils.misc import convert_grade_emoji
from utils.misc import parse_history
from utils.misc import sakuro_error
from utils.wrappers import sakuroCommand


class OsuCog(commands.Cog, name="Osu"):
    """Main bot commands."""

    def __init__(self, bot: Sakuro):
        self.bot = bot

    @sakuroCommand(
        aliases=["gm"],
        brief="Shows specific match info",
        help="Shows full history of specific match and sends it as embed.",
        usage=f"`{config.PREFIX}getmatch <match ID>`",
    )
    async def getmatch(self, ctx: ContextWrap, match_id: int) -> None:
        async with glob.http.get(
            f"https://api.sakuru.pw/get_match?id={match_id}"
        ) as resp:
            if resp and resp.status == 200 and resp.content.total_bytes != 2:
                data = (await resp.json())["match"]

                paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
                    ctx, remove_reactions=True, timeout=120
                )

                paginator.add_reaction("⏮️", "first")
                paginator.add_reaction("⏪", "back")
                paginator.add_reaction("🔐", "lock")
                paginator.add_reaction("⏩", "next")
                paginator.add_reaction("⏭️", "last")

                embed = Embed(title=f'♿ Match {data["name"]}', color=0x2ECC71)

                start_timestamp = datetime.fromtimestamp(data["created_at"])
                end_timestamp = (
                    datetime.fromtimestamp(data["closed_at"])
                    if data["closed_at"] is not None
                    else None
                )

                embed.set_footer(
                    text=f'Match start at: {start_timestamp.strftime("%c")}'
                    if end_timestamp is None
                    else f'Match start at: {start_timestamp.strftime("%c")}; Match ended at: {end_timestamp.strftime("%c")};'
                )

                embeds = []
                description = ""
                total_score = [0, 0]

                # Get unique users info
                users = {
                    x: await UserHelper.getOsuUserById(x, "info")
                    for x in set(
                        [
                            int(x["new_value"])
                            for x in data["history"]
                            if x["type"] == "player_join"
                        ]
                    )
                }

                for idx, enrty in enumerate(data["history"]):
                    temp_desc = ""

                    if enrty["type"] != "game_played":
                        temp_desc += f"\n{parse_history(enrty['type'], enrty['old_value'], enrty['new_value'], users)}"
                    else:
                        game_data = discord.utils.find(
                            lambda x: x["game_id"] == int(enrty["new_value"]),
                            data["games"],
                        )

                        req = await glob.http.get(
                            "https://api.sakuru.pw/get_map_info",
                            params={"id": game_data["beatmap_id"]},
                        )
                        bmap = (await req.json())["map"]

                        temp_desc += (
                            f"\n🎲 Game played <t:{game_data['start_time']}:f>\n"
                            f"🗺️ {bmap['artist']} - {bmap['title']} [{bmap['version']}]\n\n"
                        )

                        if game_data["team_type"] > 1:
                            blue, red = [
                                x for x in game_data["scores"] if x["team"] == 1
                            ], [x for x in game_data["scores"] if x["team"] == 2]

                            if game_data["win_condition"] in (0, 3):
                                blues_score, reds_score = sum(
                                    x["score"] for x in blue
                                ), sum(x["score"] for x in red)

                                winner = int(blues_score > reds_score)
                                total_score[winner] += 1
                            elif game_data["win_condition"] == 1:
                                pass

                            temp_desc += (
                                "🔵 Blue team\n"
                                if winner == 0
                                else "🔵 Blue team | 🥳 Winner!\n"
                            )
                            for score in blue:
                                temp_desc += (
                                    f"`{users[score['userid']]['name']}` {score['score']} {score['acc']:.2f}% "
                                    f"{convert_grade_emoji(score['grade'])} +{Mods(score['enabled_mods'] + game_data['mods'])!r}\n"
                                )

                            temp_desc += (
                                "\n🔴 Red team\n"
                                if winner != 0
                                else "\n🔴 Red team | 🥳 Winner!\n"
                            )
                            for score in red:
                                temp_desc += (
                                    f"`{users[score['userid']]['name']}` {score['score']} {score['acc']:.2f}% "
                                    f"{convert_grade_emoji(score['grade'])} +{Mods(score['enabled_mods'] + game_data['mods'])!r}\n"
                                )
                        else:
                            for score in game_data["scores"]:
                                temp_desc += (
                                    f"`{users[score['userid']]['name']}` {score['score']} {score['acc']:.2f}% "
                                    f"{convert_grade_emoji(score['grade'])} +{Mods(score['enabled_mods'] + game_data['mods'])!r}\n"
                                )
                            temp_desc += "\n"

                    if len(description) + len(temp_desc) > 2000:
                        if len(embeds) == 0:
                            embed.description = description
                            embeds.append(copy.deepcopy(embed))
                        else:
                            embed.description = description
                            embeds.append(copy.deepcopy(embed))

                        description = "" + temp_desc
                    else:
                        if idx % len(data["history"]) == len(data["history"]) - 1:
                            description += temp_desc

                            if any([x > 0 for x in total_score]):
                                description += f"\n\n**Total score:** `Blue`: {total_score[0]} | `Red`: {total_score[1]}"

                            embed.description = description
                            embeds.append(copy.deepcopy(embed))
                        else:
                            description += temp_desc

                if len(embeds) == 0:
                    embed.description = description
                    await ctx.send(embed=embed)
                else:
                    await paginator.run(embeds)
            else:
                await ctx.send(
                    sakuro_error(
                        title="Error!",
                        error=f"Match with `{match_id}` not found!",
                        color=ctx.author.color,
                    )
                )


async def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    await bot.add_cog(OsuCog(bot))
