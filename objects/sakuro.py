# -*- coding: utf-8 -*-

__all__ = (
    'ContextWrap',
    'Sakuro',
    'CommandWrap'
)

import asyncio
import functools
import os
import time
import traceback
from collections import defaultdict
from sys import exc_info
from typing import Optional

import aiohttp
import discord
import orjson
from cmyui import Version, log, Ansi
from discord.ext import commands, tasks
from discord.ext.commands import errors, CommandError
from tinydb import TinyDB

from objects import glob, config
from utils.misc import sakuro_error


def sakuro_wrapped_callback(command, ctx, coro):
    @functools.wraps(coro)
    async def wrapped(*args, **kwargs):
        try:
            ret = await coro(*args, **kwargs)
        except (Exception, CommandError, asyncio.CancelledError):
            ctx.command_failed = True

            err = exc_info()
            tb = ''.join(traceback.format_tb(err[2]))
            log(f"Unknown error occurred: {err[1]}\n{tb}", Ansi.RED)

            return await ctx.send(embed=sakuro_error(
                title="Critical error was occurred!",
                error="Please, report it! [Discord](https://discord.gg/N7NVbrJDcx) " +
                      "[GitHub](https://github.com/osu-Sakuru/sakuro/issues)\n\n" +
                      f"Error: `{err[1]}`\n```sh\n{tb}\n```",
                color=ctx.author.color
            ))
        finally:
            if command._max_concurrency is not None:
                await command._max_concurrency.release(ctx)

            await command.call_after_hooks(ctx)
        return ret

    return wrapped

class CommandWrap(commands.Command):
    async def invoke(self, ctx):
        await self.prepare(ctx)

        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = sakuro_wrapped_callback(self, ctx, self.callback)
        await injected(*ctx.args, **ctx.kwargs)

class ContextWrap(commands.Context):
    async def send(self, *args, **kwargs) -> Optional[discord.Message]:
        if len(args) == 1 and isinstance(args[0], str):
            kwargs['content'] = args[0]

        kwargs['embed'] = kwargs.pop('embed', None)
        kwargs['content'] = kwargs.pop('content', None)

        cached = self.bot.cache['responses'][self.message.id]

        if cached and (time.time() - cached['timeout']) <= 0:
            msg = cached['resp']
            await msg.edit(**kwargs)
        else:
            msg = await super().send(**kwargs)

            self.bot.cache['responses'][self.message.id] = {
                'resp': msg,
                'timeout': int(time.time()) + 300  # 5 min
            }

        return msg


class Sakuro(commands.Bot):
    __slots__ = ('loop', 'cache', 'version', 'uptime')

    def __init__(self, **kwargs) -> None:
        super().__init__(
            owner_id=config.OWNER,
            command_prefix=self.when_mentioned_or_prefix(),
            help_command=None, **kwargs
        )

        self.cache = {
            'responses': defaultdict(lambda: None),
            'latest_maps': defaultdict(lambda: None)
        }

        self.version = Version(1, 1, 0)
        self.uptime: Optional[int] = None

    def when_mentioned_or_prefix(self):
        def inner(bot, msg):
            prefix = config.PREFIX
            return commands.when_mentioned_or(prefix)(bot, msg)

        return inner

    # Custom error handler implementation
    async def invoke(self, ctx):
        if ctx.command is not None:
            self.dispatch('command', ctx)
            if await self.can_run(ctx, call_once=True):
                await ctx.command.invoke(ctx)
            else:
                raise errors.CheckFailure('The global check once functions failed.')
            self.dispatch('command_completion', ctx)
        elif ctx.invoked_with:
            exc = errors.CommandNotFound('Command "{}" is not found'.format(ctx.invoked_with))
            self.dispatch('command_error', ctx, exc)

    async def on_message_edit(self, before: discord.Message,
                              after: discord.Message) -> None:
        await self.wait_until_ready()

        if not after.content or after.author.bot:
            return

        if after.content == before.content:
            return

        if config.PUBLIC or await self.is_owner(after.author):
            await self.process_commands(after)

    async def on_message_delete(self, msg: discord.Message) -> None:
        cached = self.cache['responses'][msg.id]

        if cached:
            try:
                await cached['resp'].delete()
            except discord.NotFound:
                pass

            del self.cache['responses'][msg.id]

    async def on_ready(self) -> None:
        self.uptime = time.time()

    async def close(self) -> None:
        await super().close()

        self.loop.stop()

    async def process_commands(self, message: discord.Message):
        if not message.author.bot:
            ctx = await self.get_context(message, cls=ContextWrap)
            await self.invoke(ctx)

    async def on_command_error(self, ctx: ContextWrap, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(embed=sakuro_error(
                title="Command not found!",
                error=f"Check your spelling or type `{config.PREFIX}help`",
                color=ctx.author.color
            ))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=sakuro_error(
                title="Error!",
                error=f"Check your spelling or type `{config.PREFIX}help`\n\nError: `{error}`",
                color=ctx.author.color
            ))
        else:
            return

    @tasks.loop(seconds=20)
    async def reroll_status(self) -> None:
        await self.wait_until_ready()

        async with glob.http.get("https://osu.sakuru.pw/api/get_player_count") as resp:
            if resp.status == 200:
                data = (await resp.json())['counts']
                await self.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.watching,
                                              name=f"Sakuru online: {data['online']} Total: {data['total']}")
                )
            else:
                log('Error while rerolling bot status', Ansi.RED)

    @tasks.loop(seconds=30)
    async def check_donors(self) -> None:
        await self.wait_until_ready()

        async with glob.http.get("https://osu.sakuru.pw/api/get_donors", params={
            'secret': config.API_SECRET
        }) as resp:
            data = await resp.json()
            guild = self.get_guild(config.SAKURU_ID)

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

    def run(self, *args, **kwargs) -> None:
        async def runner() -> None:
            glob.client = Sakuro

            # ## DATABASE CONNECT ## #
            log('Settinng up database...', Ansi.MAGENTA)
            glob.db = TinyDB('./db/database.json')
            log('Database ready!', Ansi.LGREEN)
            # ## DATABASE CONNECT END ## #

            # ## HTTP SESSION ## #
            glob.http = aiohttp.ClientSession(json_serialize=orjson.dumps)
            log('Created HTTP session!', Ansi.LGREEN)
            # ## HTTP SESSION END ## #

            log('Initiating Cogs...', Ansi.LMAGENTA)
            for cog_dir in os.listdir('./cogs'):
                for file in os.listdir(f"./cogs/{cog_dir}"):
                    if file.endswith('py'):
                        self.load_extension(f"cogs.{cog_dir}.{file[:-3]}")
            log('Initiated Cogs!', Ansi.LGREEN)

            try:
                # start the bot in discordpy
                await self.start(config.TOKEN,
                                 *args, **kwargs)
            finally:
                await glob.http.close()

                glob.db.close()

                await self.close()

        self.loop = asyncio.get_event_loop()
        self.loop.create_task(runner())

        try:
            self.check_donors.start()
            self.reroll_status.start()
            self.loop.run_forever()
        finally:
            self.check_donors.cancel()
            self.reroll_status.cancel()
