# -*- coding: utf-8 -*-

__all__ = ('reroll_bot_status',)

import asyncio

import discord
from cmyui import log, Ansi

from utils import glob

async def reroll_bot_status():
    while True:
        await asyncio.sleep(25)
        async with glob.http.get("https://osu.sakuru.pw/api/get_player_count") as resp:
            if resp.status == 200:
                data = (await resp.json())['counts']
                await glob.client.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.watching,
                                              name=f"Sakuru online: {data['online']} Total: {data['total']}")
                )
            else:
                log('Error while rerolling bot status', Ansi.RED)
