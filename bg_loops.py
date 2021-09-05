# -*- coding: utf-8 -*-

__all__ = ('reroll_bot_status', 'check_donors')

import asyncio
import time

import discord
from cmyui import log, Ansi

from utils import glob, config


async def reroll_bot_status():
    while True:
        async with glob.http.get("https://osu.sakuru.pw/api/get_player_count") as resp:
            if resp.status == 200:
                data = (await resp.json())['counts']
                await glob.client.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.watching,
                                              name=f"Sakuru online: {data['online']} Total: {data['total']}")
                )
            else:
                log('Error while rerolling bot status', Ansi.RED)

        await asyncio.sleep(25)

async def check_donors():
    while True:
        async with glob.http.get("https://osu.sakuru.pw/api/get_donors", params={
            'secret': config.API_SECRET
        }) as resp:
            data = await resp.json()
            guild = glob.client.get_guild(809926238851825716)

            role = discord.utils.find(
                lambda r: r.name == "Premium",
                guild.roles
            )

            for member in guild.members:
                donor = discord.utils.find(
                    lambda x: x['discord_id'] == member.id,
                    data
                )

                is_expired = donor['donor_end'] < int(time.time()) if donor is not None else None

                if role in member.roles:
                    if donor is None:
                        await member.remove_roles(role)
                    else:
                        if is_expired:
                            await member.remove_roles(role)
                elif (
                      donor is not None and
                      role not in member.roles and
                      not is_expired
                ):
                    await member.add_roles(role)

        await asyncio.sleep(30)
