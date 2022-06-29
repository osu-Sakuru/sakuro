# -*- coding: utf-8 -*-
import copy
import platform
import time
from datetime import datetime
from datetime import timedelta
from random import choice

import discord
import timeago
from cmyui import Ansi
from cmyui import log
from discord import Embed
from discord.ext import commands

from objects import config
from objects import glob
from objects.sakuro import ContextWrap
from objects.sakuro import Sakuro
from utils.wrappers import sakuroCommand

BASE_HELP = (
    f"**Prefix:** `{config.PREFIX}` or mention the bot.\n**__General info__**\n- If you want to know more about specific "
    f'command use `{config.PREFIX}help [command].`\n- If you want to specify argument with spaces, use "" i.e '
    '`"im a fancy lad"`.\n- If you are experiencing problems or errors when using the bot, let me know! '
    "[Discord](https://discord.gg/N7NVbrJDcx) [GitHub](https://github.com/osu-Sakuru/sakuro/issues)\n"
    "- Explanation of command usage: Arguments are separated by spaces, if argument is in `[]` it means that argument "
    "is optional; `<>` means that argument is required; `/` means *one of them*.\n"
    f"- Commands that requires multiple arguments, using `-` prefix i.e.\n`{config.PREFIX}rs alowave -rx -std `\n"
    f"`{config.PREFIX}map -dthdhr -98.5 -2`\n\n__**All commands:**__\n\n"
)


class MiscCog(commands.Cog, name="Misc"):
    """Misc commands without context."""

    def __init__(self, bot: Sakuro):
        self.bot = bot

    @sakuroCommand(
        help="Really, **do not use that.**",
        brief="Command for testing some things (do not use.)",
        usage="<that> (those) [this]",
    )
    async def test(self, ctx: ContextWrap):
        pass

    @sakuroCommand(
        brief="Info about Sakuru.pw",
        help="Yes!",
        usage=f"`{config.PREFIX}info`",
        aliases=["stat", "stats"],
    )
    async def info(self, ctx: ContextWrap):
        embed = Embed(color=ctx.author.color)
        embed.set_thumbnail(url=self.bot.user.avatar.url)

        embed.add_field(
            name="About us!",
            value="Sakuru.pw is private osu server, based on [gulag](https://github.com/cmyui/gulag) "
            + "software. Sakuro it's our discord bot primarily made for osu! stuff (like recent scores etc.) "
            + "but also it have some helpful stuff like role control for a donations and etc. if you want "
            + f"support us dm me <@{config.OWNER}>.",
            inline=False,
        )

        embed.add_field(
            name="Python version",
            value=f"{platform.python_implementation()} v{platform.python_version()}",
        )

        embed.add_field(
            name="discord.py version",
            value=f"[{discord.__version__}](https://github.com/Rapptz/discord.py)",
        )

        embed.add_field(
            name="PP system",
            value=f"[Oppai-ng wrapper](https://github.com/cmyui/cmyui_pkg)",
        )

        diff = time.time() - self.bot.uptime
        embed.add_field(name="Uptime", value=f"{timedelta(seconds=int(diff))!s}")

        async with glob.http.get("https://api.sakuru.pw/get_player_count") as resp:
            if resp.status == 200:
                data = (await resp.json())["counts"]
                embed.add_field(name="Total registered", value=data["total"])
            else:
                pass

        embed.add_field(name="Bot version", value=self.bot.version)

        embed.add_field(
            name="Thank you!",
            value="Thank you for you reading this, thank you all who supported Sakuru on early and thanks "
            + "to who supporting it now, because of you i have motivation to do things!",
        )

        embed.set_footer(
            text=f"Sakuru was created {timeago.format(1613160738, time.time())}!"
        )

        await ctx.send(embed=embed)

    @sakuroCommand(
        brief="Your best friend",
        help="An ancient power created to help all mankind from the torment of the question `how does it work?`",
        usage=f"`{config.PREFIX}help`",
    )
    async def help(self, ctx: ContextWrap, input: str = None):
        description = BASE_HELP
        embed = Embed(color=ctx.author.color, description=description)

        if input is None:
            for cog in self.bot.cogs:
                cog_class = self.bot.cogs[cog]

                if getattr(cog_class, "hide", False):
                    continue

                cog_commands = cog_class.get_commands()

                if not cog_commands:
                    continue

                description += f"__**{cog}:**__ {cog_class.__doc__}\n"

                for cog_command in cog_commands:
                    if not cog_command.hidden:
                        description += f"`{cog_command.name}`: {cog_command.brief}\n"

                description += "\n"

            embed.description = description
        else:
            command = self.bot.get_command(input.lower())

            if command is not None:
                if not command.hidden:
                    embed = Embed(
                        title=command.name,
                        timestamp=datetime.now(),
                        color=ctx.author.color,
                        description=f"{command.help}\n\n**Usage of command**\n{command.usage}\n\n"
                        + f"""{f'**Aliases**{chr(10)}{", ".join(command.aliases)}' if command.aliases else ''}""",
                    )

                    embed.set_footer(text=choice(config.WORDS))
            else:
                embed = Embed(
                    title="Nothing found!",
                    description=f"We searched up and down, but couldn't find anything like `{input}` "
                    + "amongst categories and commands!",
                    timestamp=datetime.now(),
                    color=ctx.author.color,
                )

                embed.set_thumbnail(url=choice(config.ERROR_GIFS))
                embed.set_footer(text=choice(config.WORDS))

        await ctx.send(embed=embed)


async def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    await bot.add_cog(MiscCog(bot))
