# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime

from cmyui import log, Ansi
from cmyui.osu import Mods
from discord import Embed
from discord.ext import commands
from discord.threads import Thread
from tinydb.operations import set as dbset
from tinydb.queries import Query

from objects.sakuro import Sakuro, ContextWrap
from osu.calculator import Calculator
from objects import glob, config
from utils.misc import convert_status_str, convert_str_status, make_safe_name, convert_grade_emoji, sakuru_only
from objects.user import UserHelper
from utils.wrappers import sakuroCommand
from utils.misc import BEATMAP_REGEX

QUEUE_EMOJIS = (
    '1️⃣',
    '2️⃣',
    '3️⃣',
    '4️⃣',
    '5️⃣'
)


class AdminCog(commands.Cog, name='Admin'):
    """Utilities for admins."""

    def __init__(self, bot: Sakuro):
        self.bot = bot
        self.hide = True

    @sakuroCommand(name='reload', hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx: ContextWrap, module: str):
        """Reloads a module."""
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send('\N{PISTOL}')
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @sakuroCommand(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx: ContextWrap) -> None:
        await ctx.send('Night night..')
        await self.bot.close()

    @sakuroCommand(hidden=True)
    @commands.check(sakuru_only)
    @commands.has_permissions(ban_members=True)
    async def replay(self, ctx: ContextWrap, nickname: str, mods: str, map_id: int):
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

    @sakuroCommand(hidden=True)
    @commands.check(sakuru_only)
    @commands.has_permissions(ban_members=True)
    async def restrict(self, ctx: ContextWrap, nickname: str, *reason: str):
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
                await ctx.message.add_reaction('\N{OK HAND SIGN}')
            else:
                return await ctx.send("Error occurred.")

    @sakuroCommand(hidden=True)
    @commands.check(sakuru_only)
    @commands.has_permissions(ban_members=True)
    async def unrestrict(self, ctx: ContextWrap, nickname: str, *reason: str):
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
                await ctx.message.add_reaction('\N{OK HAND SIGN}')
            else:
                return await ctx.send("Error occurred.")

    @sakuroCommand(hidden=True)
    @commands.check(sakuru_only)
    @commands.has_any_role(
        # BAT
        811271693610778645,
        # ADMIN
        811271842739519538,
        # HEAD ADMIN
        811271454519722005
    )
    async def rqmap(self, ctx: ContextWrap, status: str, type: str):
        if (
            not isinstance(ctx.message.channel, Thread) or
            not ctx.message.channel.parent_id == config.MAP_REQS
        ):
            return
        
        if ctx.message.channel.archived:
            return

        req_table = glob.db.table('map_reqs')
        
        Requests = Query()
        req = req_table.get((Requests.thread_id == ctx.message.channel.id) & (Requests.active == True))

        admin = await UserHelper.getDiscordUser(ctx.message.author.id)

        if not admin:
            return await ctx.send('who are yo')
        
        if type not in ('map', 'set'):
            msg = await ctx.reply('Invalid type! (map, set)')

            await msg.delete(delay=15)
            await ctx.message.delete(delay=15)
            return
        
        if status not in ('love', 'rank', 'unrank'):
            msg = await ctx.reply('Invalid status! (love, rank, unrank)')

            await msg.delete(delay=15)
            await ctx.message.delete(delay=15)
            return

        if type == "map":            
            params = {
                "set_id": req['beatmap']['set_id']
            }

            async with glob.http.get("https://osu.sakuru.pw/api/get_map_info", params=params) as resp:
                if (
                        resp and resp.status == 200 and
                        resp.content.total_bytes != 2  # b'[]'
                ):
                    bmaps = await resp.json()

                    embed = Embed(
                        title=f"Pick a map to edit status on.",
                        timestamp=datetime.now(),
                        color=0xeaff00
                    )

                    description = ""
                    for idx, bmap in enumerate(bmaps['set']):
                        description += f"`#{idx + 1}.` **[{bmap['version']}]** - {convert_status_str(int(bmap['status']))}\n"
                    
                    embed.description = description
                    emb_mess = await ctx.send("**Send position in chat to pick a map.**", embed=embed)
            
            valid = False
            while valid is False:
                try:
                    reply = await self.bot.wait_for('message', check=lambda x: x.channel == ctx.channel and x.author == ctx.author and x.content.isdecimal(), 
                                                               timeout=60.0)
                except asyncio.TimeoutError:
                    msg = await ctx.send('Time is up!')

                    await msg.delete(delay=15)
                    await emb_mess.delete(delay=15)
                    return
                else:
                    reply.content = int(reply.content)
                    if reply.content > len(bmaps) or reply.content <= 0:
                        msg = await ctx.send('Specified position is out of range.')
                        
                        await reply.delete(delay=15)
                        await msg.delete(delay=15)
                    else:
                        if (bm_status := bmaps['set'][reply.content - 1]['status']) == convert_str_status(status):
                            msg = await ctx.send(f"This map is already {convert_status_str(bm_status)}")
                            
                            await msg.delete(delay=15)
                            await reply.delete(delay=15)
                        else:
                            await reply.delete()
                            await emb_mess.delete()

                            valid = True
            
            params = {
                "secret": config.API_SECRET,
                "action": "status_map",
                "admin": admin['safe_name'],
                "map_id": bmaps['set'][reply.content - 1]['id'],
                "status": status
            }
            async with glob.http.get("https://osu.sakuru.pw/api/handle_admin", params=params) as resp:
                if resp.status == 200:
                    await ctx.message.add_reaction('\N{OK HAND SIGN}')
                else:
                    pass

        elif type =="set":
            params = {
                "set_id": req['beatmap']['set_id']
            }

            async with glob.http.get("https://osu.sakuru.pw/api/get_map_info", params=params) as resp:
                if (
                        resp and resp.status == 200 and
                        resp.content.total_bytes != 2  # b'[]'
                ):
                    bmaps = await resp.json()
                    

                    if all([x['status'] == convert_str_status(status) for x in bmaps['set']]):
                        msg = await ctx.send(f"This set is already {convert_status_str(bmaps['set'][0]['status'])}")

                        await ctx.message.delete(delay=15)
                        await msg.delete(delay=15)
                        return

            params = {
                "secret": config.API_SECRET,
                "action": "status_set",
                "admin": admin['safe_name'],
                "set_id": req['beatmap']['set_id'],
                "status": status
            }

            async with glob.http.get("https://osu.sakuru.pw/api/handle_admin", params=params) as resp:
                if resp.status == 200:
                    await ctx.message.add_reaction('\N{OK HAND SIGN}')
                else:
                    pass

    @sakuroCommand(hidden=True)
    @commands.check(sakuru_only)
    @commands.has_any_role(
        # BAT
        811271693610778645,
        # ADMIN
        811271842739519538,
        # HEAD ADMIN
        811271454519722005
    )
    async def rqclose(self, ctx: ContextWrap):
        if (
            not isinstance(ctx.message.channel, Thread) or
            not ctx.message.channel.parent_id == config.MAP_REQS
        ):
            return

        if ctx.message.channel.archived:
            return
        
        req_table = glob.db.table('map_reqs')
        
        Requests = Query()
        req = req_table.get((Requests.thread_id == ctx.message.channel.id) & (Requests.active == True))
        
        req_table.update(
            dbset('active', False),
            doc_ids=[req.doc_id]
        )
        
        first_message = await ctx.message.channel.parent.fetch_message(req['original_id'])
        
        await first_message.delete()
        await ctx.channel.delete()
    
    @sakuroCommand(hidden=True)
    @commands.check(sakuru_only)
    @commands.has_any_role(
        # BAT
        811271693610778645,
        # ADMIN
        811271842739519538,
        # HEAD ADMIN
        811271454519722005
    )
    async def rqreject(self, ctx: ContextWrap, *reason: str):
        if (
            not isinstance(ctx.message.channel, Thread) or
            not ctx.message.channel.parent_id == config.MAP_REQS
        ):
            return
        
        if ctx.message.channel.archived:
            return

        req_table = glob.db.table('map_reqs')
        
        Requests = Query()
        req = req_table.get((Requests.thread_id == ctx.message.channel.id) & (Requests.active == True))

        first_message = await ctx.message.channel.parent.fetch_message(req['original_id'])
        requester = ctx.guild.get_member(req['requester'])

        params = {
            "id": req['beatmap']['id']
        }
        async with glob.http.get("https://osu.sakuru.pw/api/get_map_info", params=params) as resp:
            if (
                resp and resp.status == 200 and
                resp.content.total_bytes != 2  # b'[]'
            ):
                bmap = (await resp.json())['map']
                embed = Embed(
                    title=f"Map Request: {bmap['artist']} - {bmap['title']}",
                    color=ctx.author.color,
                    description=f"Your request has been rejected!\n**Reason:** `{' '.join(reason)}`\n\n**Nominator:** {ctx.author.mention}",
                    timestamp=datetime.now()
                )

                embed.set_footer(text="Sakuru.pw osu! Private Server.")
                embed.set_thumbnail(url=ctx.author.avatar.url)


                await requester.send(embed=embed)

        req_table.update(
            dbset('active', False),
            doc_ids=[req.doc_id]
        )

        await first_message.delete()
        await ctx.channel.delete()

def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(AdminCog(bot))
