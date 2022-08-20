# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime

from cmyui import Ansi
from cmyui import log
from cmyui.osu import Mods
from discord import Embed
from discord.ext import commands
from discord.threads import Thread
from tinydb.operations import set as dbset
from tinydb.queries import Query

from objects import config
from objects import glob
from objects.sakuro import ContextWrap
from objects.sakuro import Sakuro
from objects.user import UserHelper
from utils.misc import convert_grade_emoji
from utils.misc import convert_status_str
from utils.misc import convert_str_status
from utils.misc import make_safe_name
from utils.misc import sakuru_only
from utils.wrappers import sakuroCommand

QUEUE_EMOJIS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣")


class AdminCog(commands.Cog, name="Admin"):
    """Utilities for admins."""

    def __init__(self, bot: Sakuro):
        self.bot = bot
        self.hide = True

    @sakuroCommand(name="reload", hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx: ContextWrap, module: str):
        """Reloads a module."""
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send("\N{PISTOL}")
            await ctx.send("{}: {}".format(type(e).__name__, e))
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @sakuroCommand(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx: ContextWrap) -> None:
        await ctx.send("Night night..")
        await self.bot.close()

    @sakuroCommand(hidden=True)
    @commands.check(sakuru_only)
    @commands.has_permissions(ban_members=True)
    async def restrict(self, ctx: ContextWrap, nickname: str, *reason: str):
        if not await UserHelper.getOsuUserByName(make_safe_name(nickname), "info"):
            return await ctx.send(f"Player with nickname {nickname} not found.")

        admin = await UserHelper.getDiscordUser(ctx.message.author.id)

        async with glob.http.post(
            "https://api.sakuru.pw/handle_admin",
            params={
                "secret": config.API_SECRET,
                "action": "restrict",
                "nickname": make_safe_name(nickname),
                "reason": " ".join(reason),
                "admin": admin["safe_name"],
            },
        ) as resp:
            if resp.status == 200:
                await ctx.message.add_reaction("\N{OK HAND SIGN}")
            else:
                return await ctx.send("Error occurred.")

    @sakuroCommand(hidden=True)
    @commands.check(sakuru_only)
    @commands.has_permissions(ban_members=True)
    async def wipe(self, ctx: ContextWrap, nickname: str):
        if not await UserHelper.getOsuUserByName(make_safe_name(nickname), "info"):
            return await ctx.send(f"Player with nickname {nickname} not found.")

        admin = await UserHelper.getDiscordUser(ctx.message.author.id)

        async with glob.http.post(
            "https://api.sakuru.pw/handle_admin",
            params={
                "secret": config.API_SECRET,
                "action": "wipe",
                "nickname": make_safe_name(nickname),
                "admin": admin["safe_name"],
            },
        ) as resp:
            if resp.status == 200:
                await ctx.message.add_reaction("\N{OK HAND SIGN}")
            else:
                return await ctx.send("Error occurred.")

    @sakuroCommand(hidden=True)
    @commands.check(sakuru_only)
    @commands.has_permissions(ban_members=True)
    async def unrestrict(self, ctx: ContextWrap, nickname: str, *reason: str):
        if not await UserHelper.getOsuUserByName(make_safe_name(nickname), "info"):
            return await ctx.send(f"Player with nickname {nickname} not found.")

        admin = await UserHelper.getDiscordUser(ctx.message.author.id)

        async with glob.http.post(
            "https://api.sakuru.pw/handle_admin",
            params={
                "secret": config.API_SECRET,
                "action": "unrestrict",
                "nickname": make_safe_name(nickname),
                "reason": " ".join(reason),
                "admin": admin["safe_name"],
            },
        ) as resp:
            if resp.status == 200:
                await ctx.message.add_reaction("\N{OK HAND SIGN}")
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
        811271454519722005,
    )
    async def rqmap(self, ctx: ContextWrap, status: str, type: str):
        if (
            not isinstance(ctx.message.channel, Thread)
            or not ctx.message.channel.parent_id == config.MAP_REQS
        ):
            return

        if ctx.message.channel.archived:
            return

        req_table = glob.db.table("map_reqs")

        Requests = Query()
        req = req_table.get(
            (Requests.thread_id == ctx.message.channel.id) & (Requests.active == True)
        )

        admin = await UserHelper.getDiscordUser(ctx.message.author.id)

        if not admin:
            return await ctx.send("who are yo")

        if type not in ("map", "set"):
            msg = await ctx.reply("Invalid type! (map, set)")

            await msg.delete(delay=15)
            await ctx.message.delete(delay=15)
            return

        if status not in ("love", "rank", "unrank"):
            msg = await ctx.reply("Invalid status! (love, rank, unrank)")

            await msg.delete(delay=15)
            await ctx.message.delete(delay=15)
            return

        if type == "map":
            params = {"set_id": req["beatmap"]["set_id"]}

            async with glob.http.get(
                "https://api.sakuru.pw/get_map_info", params=params
            ) as resp:
                if (
                    resp
                    and resp.status == 200
                    and resp.content.total_bytes != 2  # b'[]'
                ):
                    bmaps = await resp.json()

                    embed = Embed(
                        title=f"Pick a map to edit status on.",
                        timestamp=datetime.now(),
                        color=0xEAFF00,
                    )

                    description = ""
                    for idx, bmap in enumerate(bmaps["map"]):
                        description += f"`#{idx + 1}.` **[{bmap['version']}]** - {convert_status_str(int(bmap['status']))}\n"

                    embed.description = description
                    emb_mess = await ctx.send(
                        "**Send position in chat to pick a map.**", embed=embed
                    )

            valid = False
            while valid is False:
                try:
                    reply = await self.bot.wait_for(
                        "message",
                        check=lambda x: x.channel == ctx.channel
                        and x.author == ctx.author
                        and x.content.isdecimal(),
                        timeout=60.0,
                    )
                except asyncio.TimeoutError:
                    msg = await ctx.send("Time is up!")

                    await msg.delete(delay=15)
                    await emb_mess.delete(delay=15)
                    return
                else:
                    user_reply_parse = int(reply.content)

                    if user_reply_parse > len(bmaps["map"]) or user_reply_parse <= 0:
                        msg = await ctx.send("Specified position is out of range.")

                        await reply.delete(delay=15)
                        await msg.delete(delay=15)
                    else:
                        if (
                            bm_status := bmaps["map"][user_reply_parse - 1]["status"]
                        ) == convert_str_status(status):
                            msg = await ctx.send(
                                f"This map is already {convert_status_str(bm_status)}"
                            )

                            await msg.delete(delay=15)
                            await reply.delete(delay=15)
                        else:
                            await reply.delete()
                            await emb_mess.delete()

                            valid = True

            params = {
                "secret": config.API_SECRET,
                "action": "status_map",
                "admin": admin["safe_name"],
                "map_id": bmaps["map"][user_reply_parse - 1]["id"],
                "map_status": status,
            }
            async with glob.http.post(
                "https://api.sakuru.pw/handle_admin", params=params
            ) as resp:
                if resp.status == 200:
                    await ctx.message.add_reaction("\N{OK HAND SIGN}")
                else:
                    pass

        elif type == "set":
            params = {"set_id": req["beatmap"]["set_id"]}

            async with glob.http.get(
                "https://api.sakuru.pw/get_map_info", params=params
            ) as resp:
                if (
                    resp
                    and resp.status == 200
                    and resp.content.total_bytes != 2  # b'[]'
                ):
                    bmaps = await resp.json()

                    if all(
                        [
                            x["status"] == convert_str_status(status)
                            for x in bmaps["map"]
                        ]
                    ):
                        msg = await ctx.send(
                            f"This set is already {convert_status_str(bmaps['map'][0]['status'])}"
                        )

                        await ctx.message.delete(delay=15)
                        await msg.delete(delay=15)
                        return

            params = {
                "secret": config.API_SECRET,
                "action": "status_set",
                "admin": admin["safe_name"],
                "set_id": req["beatmap"]["set_id"],
                "map_status": status,
            }

            async with glob.http.post(
                "https://api.sakuru.pw/handle_admin", params=params
            ) as resp:
                if resp.status == 200:
                    await ctx.message.add_reaction("\N{OK HAND SIGN}")
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
        811271454519722005,
    )
    async def rqclose(self, ctx: ContextWrap):
        if (
            not isinstance(ctx.message.channel, Thread)
            or not ctx.message.channel.parent_id == config.MAP_REQS
        ):
            return

        if ctx.message.channel.archived:
            return

        req_table = glob.db.table("map_reqs")

        Requests = Query()
        req = req_table.get(
            (Requests.thread_id == ctx.message.channel.id) & (Requests.active == True)
        )

        req_table.update(dbset("active", False), doc_ids=[req.doc_id])

        first_message = await ctx.message.channel.parent.fetch_message(
            req["original_id"]
        )

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
        811271454519722005,
    )
    async def rqreject(self, ctx: ContextWrap, *reason: str):
        if (
            not isinstance(ctx.message.channel, Thread)
            or not ctx.message.channel.parent_id == config.MAP_REQS
        ):
            return

        if ctx.message.channel.archived:
            return

        req_table = glob.db.table("map_reqs")

        Requests = Query()
        req = req_table.get(
            (Requests.thread_id == ctx.message.channel.id) & (Requests.active == True)
        )

        first_message = await ctx.message.channel.parent.fetch_message(
            req["original_id"]
        )
        requester = ctx.guild.get_member(req["requester"])

        params = {"id": req["beatmap"]["id"]}
        async with glob.http.get(
            "https://api.sakuru.pw/get_map_info", params=params
        ) as resp:
            if resp and resp.status == 200 and resp.content.total_bytes != 2:  # b'[]'
                bmap = (await resp.json())["map"]
                embed = Embed(
                    title=f"Map Request: {bmap['artist']} - {bmap['title']}",
                    color=ctx.author.color,
                    description=f"Your request has been rejected!\n**Reason:** `{' '.join(reason)}`\n\n**Nominator:** {ctx.author.mention}",
                    timestamp=datetime.now(),
                )

                embed.set_footer(text="Sakuru.pw osu! Private Server.")
                embed.set_thumbnail(url=ctx.author.avatar.url)

                await requester.send(embed=embed)

        req_table.update(dbset("active", False), doc_ids=[req.doc_id])

        await first_message.delete()
        await ctx.channel.delete()


async def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    await bot.add_cog(AdminCog(bot))
