# -*- coding: utf-8 -*-
from datetime import datetime
from random import choice

from cmyui import log, Ansi
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context

from utils import config

BASE_HELP = (
        f"**Prefix:** `{config.PREFIX}`\n**__General info__**\n- If you want to know more about specific " +
        f"command use `{config.PREFIX}help [command].`\n- If you want to specify argument with spaces, use \"\" i.e " +
        "`\"im a fancy lad\"`.\n- If you are experiencing problems or errors when using the bot, let me know! " +
        "[Discord](https://discord.gg/N7NVbrJDcx) [GitHub](https://github.com/osu-Sakuru/sakuro/issues)\n" +
        f"- Commands that requires multiple arguments, using `-` prefix i.e.\n`{config.PREFIX}rs alowave -std -rx`\n" +
        f"`{config.PREFIX}map -dthdhr -98.5 -2`\n\n__**All commands:**__\n\n"
)

class MiscCog(commands.Cog, name='Misc'):
    """Misc commands without context."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        help="Really, **do not use that.**",
        brief="Command for testing some things (do not use.)",
        usage="<that> (those) [this]"
    )
    async def test(self, ctx: Context):
        print(self.bot.get_command('test').usage)
        await ctx.send("**Test**")

    @commands.command(
        brief="Your best friend",
        help="An ancient power created to help all mankind from the torment of the question `how does it work?`",
        usage=f"`{config.PREFIX}help`"
    )
    async def help(self, ctx: Context, input: str = None):
        description = BASE_HELP
        embed = Embed(color=ctx.author.color, description=description)

        if input is None:
            for cog in self.bot.cogs:
                cog_class = self.bot.cogs[cog]

                if getattr(cog_class, 'hide', False):
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
            for cog in self.bot.cogs:
                if cog.lower() == input.lower():
                    cog_class = self.bot.cogs[cog]

                    if getattr(cog_class, 'hide', False):
                        continue

                    cog_commands = cog_class.get_commands()

                    if not cog_commands:
                        continue

                    description += f"__**{cog}:**__ {cog_class.__doc__}\n"

                    for cog_command in cog_commands:
                        if not cog_command.hidden:
                            description += f"`{cog_command.name}`: {cog_command.brief}\n"
                    # Found!
                    break
            else:
                command = self.bot.get_command(input.lower())

                if command is not None:
                    if not command.hidden:
                        embed = Embed(title=command.name,
                                      timestamp=datetime.now(),
                                      color=ctx.author.color,
                                      description=f"{command.help}\n\n**Usage of command**\n{command.usage}\n\n" +
                                                  f"""{f'**Aliases**{chr(10)}{", ".join(command.aliases)}' if command.aliases else ''}""")

                        embed.set_footer(text=choice(config.WORDS))
                else:
                    embed = Embed(title="Nothing found!",
                                  description=f"We searched up and down, but couldn't find anything like `{input}` " +
                                              "amongst categories and commands!",
                                  timestamp=datetime.now(),
                                  color=ctx.author.color)

                    embed.set_thumbnail(url=choice(config.ERROR_GIFS))
                    embed.set_footer(text=choice(config.WORDS))

        await ctx.send(embed=embed)


def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(MiscCog(bot))
