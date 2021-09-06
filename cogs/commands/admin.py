# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime

from cmyui import log, Ansi
from cmyui.osu import Mods
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context

from osu.calculator import Calculator
from utils import glob, config
from utils.misc import make_safe_name, convert_grade_emoji
from utils.user import UserHelper
from utils.wrappers import only_sakuru

QUEUE_EMOJIS = (
    '1️⃣',
    '2️⃣',
    '3️⃣',
    '4️⃣',
    '5️⃣'
)


class AdminCog(commands.Cog, name='Admin'):
    """Utilities for admins."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.hide = True

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

    @commands.command(hidden=True)
    @only_sakuru
    @commands.has_permissions(ban_members=True)
    async def replay(self, ctx: Context, nickname: str, mods: str, map_id: int):
        player = await UserHelper.getOsuUserByName(make_safe_name(nickname), 'info')
        description = ""

        if not player:
            async with glob.http.get("https://sakuru.pw/api/search", params={
                "q": nickname
            }) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    if data['length'] == 0:
                        return await ctx.send(f"Nothing matched with {nickname} not found, check your spelling.")

                    embed = Embed(
                        color=ctx.author.color,
                        timestamp=datetime.now()
                    )

                    embed.set_author(name=f"Search queue for {nickname}")

                    for idx, row in enumerate(data['matches']):
                        description += f"**{idx + 1}.** [{row['name']}](https://sakuru.pw/u/{row['id']})\n"

                    embed.description = description
                    description = ""
                    message = await ctx.send(embed=embed)

                    for emoji in QUEUE_EMOJIS[:data['length']]:
                        await message.add_reaction(emoji)
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add',
                                                                 check=lambda r, u: r.message.id == message.id \
                                                                                    and r.emoji in QUEUE_EMOJIS \
                                                                                    and u == ctx.author,
                                                                 timeout=60.0)
                    except asyncio.TimeoutError:
                        await ctx.send('Time is out!')
                    else:
                        player = await UserHelper.getOsuUserByName(
                            make_safe_name(
                                data['matches'][QUEUE_EMOJIS.index(reaction.emoji)]['name']),
                            'info'
                        )
                        await message.delete()
                else:
                    return await ctx.send("Error! Try again.")

        scores = await UserHelper.getUserScores(player['id'], 0, mods, 5, 'best', map_id)

        if len(scores) == 0:
            return await ctx.send(f"This player has no scores on `{map_id}`!")

        map_fullname = ""

        for idx, score in enumerate(scores):
            calc = await Calculator.calculate(
                score['beatmap']['id'],
                0,
                score['mods'],
                score['acc'],
                None
            )
            map_fullname = calc['map_fullname']

            description += f"""** {idx + 1}. {f' +{Mods(score["mods"])!r}' if score['mods'] != 0 else ''}** [{calc['stars']:.2f}★]\n""" \
                           f"▸ {convert_grade_emoji(score['grade'])} ▸ **{score['pp']:.2f}PP**" \
                           f"""{f' *({calc["pp"]:.2f}PP for {score["acc"]:.2f}% FC)*' if score['grade'] not in ('S', 'SS', 'X', 'SH') else ''} """ \
                           f"▸ {score['acc']:.2f}%\n▸ {score['score']} ▸ x{score['max_combo']}/{score['beatmap']['max_combo']} " \
                           f"▸ [{score['n300']}/{score['n100']}/{score['n50']}/{score['nmiss']}]\n" \
                           f"▸ [Score Set <t:{datetime.fromisoformat(score['play_time']).timestamp().__int__()}:R>]" \
                           f"(https://osu.sakuru.pw/api/get_replay?id={score['id']})\n"

        embed = Embed(color=ctx.author.color, description=description)

        embed.set_author(name=f"Top {len(scores)} Plays for {player['name']} on {map_fullname}",
                         url=f"https://sakuru.pw/u/{player['id']}",
                         icon_url=f"https://sakuru.pw/static/flags/{player['country'].upper()}.png")
        embed.set_footer(text="Click on Score Set to download replay.",
                         icon_url="https://sakuru.pw/static/ingame.png")

        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @only_sakuru
    @commands.has_permissions(ban_members=True)
    async def restrict(self, ctx: Context, nickname: str, *reason: str):
        if not await UserHelper.getOsuUserByName(make_safe_name(nickname), 'info'):
            return await ctx.send(f"Player with nickname {nickname} not found.")

        admin = await UserHelper.getDiscordUser(ctx.message.author.id)

        async with glob.http.get("https://osu.sakuru.pw/api/handle_admin",
                                  params={
                                      "secret": config.API_SECRET,
                                      "action": "restrict",
                                      "nickname": make_safe_name(nickname),
                                      "reason": ' '.join(reason),
                                      "admin": admin['safe_name']
                                  }) as resp:
            if resp.status == 200:
                await ctx.send(f"Banned `{nickname}` for `{' '.join(reason)}`.")
            else:
                return await ctx.send("Error occurred.")

    @commands.command(hidden=True)
    @only_sakuru
    @commands.has_permissions(ban_members=True)
    async def unrestrict(self, ctx: Context, nickname: str, *reason: str):
        if not await UserHelper.getOsuUserByName(make_safe_name(nickname), 'info'):
            return await ctx.send(f"Player with nickname {nickname} not found.")

        admin = await UserHelper.getDiscordUser(ctx.message.author.id)

        async with glob.http.get("https://osu.sakuru.pw/api/handle_admin",
                                  params={
                                      "secret": config.API_SECRET,
                                      "action": "unrestrict",
                                      "nickname": make_safe_name(nickname),
                                      "reason": ' '.join(reason),
                                      "admin": admin['safe_name']
                                  }) as resp:
            if resp.status == 200:
                await ctx.send(f"Unbanned `{nickname}` for `{' '.join(reason)}`.")
            else:
                return await ctx.send("Error occurred.")

def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(AdminCog(bot))
