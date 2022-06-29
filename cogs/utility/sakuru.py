# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from cmyui import log, Ansi
from discord import Message, message
import discord
from discord.embeds import Embed
from discord.ext import commands

from objects import config, glob
from objects.sakuro import Sakuro
from utils.misc import CHO_BEATMAP_REGEX, SAKURU_BEATMAP_REGEX, convert_status_str


class SakuruCog(commands.Cog):
    def __init__(self, bot: Sakuro):
        self.bot = bot

    @commands.Cog.listener(name="on_message")
    async def map_reqs(self, msg: Message) -> None:
        if msg.guild and msg.guild.id == config.SAKURU_ID and msg.channel.id == config.MAP_REQS and not msg.author.bot:
            if (
                (beatmap := CHO_BEATMAP_REGEX.search(msg.content)) is None and
                (beatmap := SAKURU_BEATMAP_REGEX.search(msg.content)) is None
            ):
                reply = await msg.reply("Map not found! You only able to post beatmap links in this channel. "
                                        "This message will be deleted in 30 secs.")

                await reply.delete(delay=30)
                await msg.delete(delay=30)
            else:
                if (set_id := beatmap.groupdict().get('sid', None)) is not None:
                    params = {
                        "set_id": set_id
                    }
                else:
                    params = {
                        "id": beatmap.group('bid'),
                        "set_from_map": 1
                    }

                async with glob.http.get("https://api.sakuru.pw/get_map_info", params=params) as resp:
                    if (
                        resp and resp.status == 200 and
                        resp.content.total_bytes != 2  # b'[]'
                    ):
                        bmaps_raw = (await resp.json())['map']
                        bmaps = sorted(bmaps_raw, key=lambda x: x['diff'], reverse=True)

                        first = bmaps[0]
                        chan_name = f"Conversation of {first['artist']} - {first['title']} by {first['creator']}."
                        
                        # XXX: (error code: 50035): Invalid Form Body In name: Must be 100 or fewer in length.
                        chan_name = (chan_name[:97] + '...') if len(chan_name) > 100 else chan_name

                        if discord.utils.find(lambda x: x.name == chan_name, msg.channel.threads) is not None:
                            rply = await msg.reply("This map is already requested.")

                            await rply.delete(delay=15)
                            await msg.delete(delay=15)
                            return
                        
                        thread = await msg.create_thread(name=chan_name)

                        requests = glob.db.table('map_reqs')
                        req_id = requests.insert({
                            'thread_id': thread.id,
                            'active': True,
                            'original_id': msg.id,
                            'requester': msg.author.id,
                            'beatmap': {
                                'set_id': first['set_id']
                            }
                        })
                        
                        embed = Embed(
                            title=f"Info about {first['artist']} - {first['title']}.",
                            timestamp=datetime.now(),
                            color=0xeaff00
                        )

                        description = f"**Basic info:**\n`BPM:` {first['bpm']}\n`Status:` {convert_status_str(first['status'])}\n" \
                                      f"`Length:` {timedelta(seconds = first['total_length'])}\n\n"

                        for bmap in bmaps:
                            description += f"**[{bmap['version']}]** - {bmap['diff']:.2f} ⭐ " \
                                           f"`CS:` {bmap['cs']} `OD:` {bmap['od']} `AR:` {bmap['ar']}\n" 

                        embed.description = description

                        embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{first['set_id']}/covers/cover.jpg")

                        await thread.send(f'Request ID: {req_id}', embed=embed)

async def setup(bot) -> None:
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    await bot.add_cog(SakuruCog(bot))
