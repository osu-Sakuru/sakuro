#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
from os import listdir

import aiohttp
from discord import Embed
from discord.ext import commands
from cmyui import log
from cmyui.logging import Ansi
from orjson import orjson
from tinydb import TinyDB

import utils.glob as glob
import utils.config as config

log('Starting bot...', Ansi.BLUE)

client = commands.Bot(command_prefix='$')

@client.event
async def on_ready():
    # ## DATABASE CONNECT ## #
    log('Settinng up database...', Ansi.MAGENTA)
    glob.db = TinyDB('./db/database.json')
    log('Database ready!', Ansi.LGREEN)
    # ## DATABASE CONNECT END ## #

    # ## HTTP SESSION ## #
    glob.http = aiohttp.ClientSession(json_serialize=orjson.dumps)
    log('Created HTTP session!', Ansi.LGREEN)
    # ## HTTP SESSION END ## #

    # ## COGS INIT ## #
    log('Initiating Cogs...', Ansi.LMAGENTA)
    for file in listdir("./cogs"):
        if file.endswith('.py'):
            client.load_extension(f"cogs.{file[:-3]}")
    log('Initiated Cogs!', Ansi.LGREEN)
    # ## COGS INIT END ## #

    log('Bot has been started!', Ansi.LBLUE)

@client.event
async def on_message(message):
    if message.author.bot:
        return

    await client.process_commands(message)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        em = Embed(title=f"Error!!!", description=f"Command not found.", color=ctx.author.color)
        await ctx.send(embed=em)

client.run(config.TOKEN)
