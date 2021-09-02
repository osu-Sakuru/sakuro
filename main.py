#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
import asyncio
import datetime
from os import listdir

import aiohttp
from discord import Embed, Message
from discord.ext import commands
from cmyui import log
from cmyui.logging import Ansi
from inspect import getmembers, isfunction
import orjson
from discord.ext.commands import Context
from tinydb import TinyDB
from random import choice

import bg_loops
import utils.glob as glob
import utils.config as config

log('Starting bot...', Ansi.BLUE)

client = commands.Bot(command_prefix=config.PREFIX)

@client.event
async def on_ready() -> None:
    glob.client = client

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
    log('Initiating background loops...', Ansi.LMAGENTA)
    funcs = getmembers(bg_loops, lambda x: isfunction(x) and x.__name__ in bg_loops.__all__)

    for func in funcs:
        loop = asyncio.get_running_loop()
        loop.create_task(func[1].__call__())
    log(f"Initiated {len(funcs)} background loops!", Ansi.LGREEN)
    # ## BG LOOPS END ## #

    log('Bot has been started!', Ansi.LBLUE)

@client.event
async def on_message(message: Message) -> None:
    if message.author.bot:
        return

    await client.process_commands(message)

@client.event
async def on_command_error(ctx: Context, error) -> None:
    if isinstance(error, commands.CommandNotFound):
        em = Embed(title="Command not found!",
                   description=f"Check your spelling or type `{config.PREFIX}help`",
                   color=ctx.author.color,
                   timestamp=datetime.datetime.now())

        em.set_thumbnail(url=choice(config.ERROR_GIFS))
        em.set_footer(text=choice(config.WORDS))

        await ctx.send(embed=em)
    elif isinstance(error, commands.MissingRequiredArgument):
        em = Embed(title="Error!",
                   description=f"Check your spelling or type `{config.PREFIX}help`\n\nError: `{error}`",
                   color=ctx.author.color,
                   timestamp=datetime.datetime.now())

        em.set_thumbnail(url=choice(config.ERROR_GIFS))
        em.set_footer(text=choice(config.WORDS))

        await ctx.send(embed=em)
    else:
        log(f"Unknown error occurred: {error}", Ansi.RED)

        em = Embed(title="Critical error was occurred!",
                   description="Please, report it! [Discord](https://discord.gg/N7NVbrJDcx) " +
                               "[GitHub](https://github.com/osu-Sakuru/sakuro/issues)\n\n" +
                               f"Error: `{error}`",
                   color=ctx.author.color,
                   timestamp=datetime.datetime.now())

        em.set_thumbnail(url=choice(config.ERROR_GIFS))
        em.set_footer(text=choice(config.WORDS))

        await ctx.send(embed=em)

client.run(config.TOKEN)
