import traceback
from datetime import datetime
from functools import wraps
from random import choice
from sys import exc_info

from cmyui import Ansi, log
from discord import Embed

from utils import config
from utils.user import UserHelper


def handle_exception(func) -> wraps:
    """Simple exception handler for commands."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = args[1]

        try:
            return await func(*args, **kwargs)
        except:
            err = exc_info()
            tb = ''.join(traceback.format_tb(err[2]))
            log(f"Unknown error occurred: {err[1]}\n{tb}", Ansi.RED)

            em = Embed(title="Critical error was occurred!",
                       description="Please, report it! [Discord](https://discord.gg/N7NVbrJDcx) " +
                                   "[GitHub](https://github.com/osu-Sakuru/sakuro/issues)\n\n" +
                                   f"Error: `{err[1]}`\n```sh\n{tb}\n```",
                       color=ctx.author.color,
                       timestamp=datetime.now())

            em.set_thumbnail(url=choice(config.ERROR_GIFS))
            em.set_footer(text=choice(config.WORDS))

            return await ctx.send(embed=em)

    return wrapper

def check_args(func) -> wraps:
    """Simple argument checker for commands."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Getting required arguments, skip username
        ctx, _, mods, mode = args[1:5]

        if mods not in ('vn', 'rx', 'ap'):
            return await ctx.send('Invalid mods provided! (vn, rx, ap)')

        if mode not in ('std', 'mania', 'taiko'):
            return await ctx.send('Invalid mode provided! (std, mania, taiko)')

        if mode == 'mania':
            if mods != 'vn':
                return await ctx.send('Invalid mods for mania! Only vn is allowed.')
        else:
            if mods not in ('vn', 'rx'):
                return await ctx.send('Invalid mods for taiko! Only vn and rx is allowed.')

        return await func(*args, **kwargs)

    return wrapper

def link_required(func) -> wraps:
    """Simple wrapper for command that's requires user be linked. NOTE: Use it ONLY with commands."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        name = args[2]
        ctx = args[1]

        if name is None:
            if not (data := await UserHelper.getDiscordUser(ctx.message.author.id)):
                embed = Embed(title="Notice!",
                              description="Your account should be linked with our bot to use this command. " +
                              "Please, follow [this link](https://sakuru.pw/settings/socials) to link your account.",
                              timestamp=datetime.now(), colour=0xeaff00)
                embed.set_footer(text='Sakuru.pw private osu! server.')

                return await ctx.send(embed=embed)
            else:
                args = args[:2] + (data,) + args[3:]
        else:
            if not (data := await UserHelper.getOsuUserByName(name, "info")):
                return await ctx.send(f"User `{name}` not found or didn't exists.")
            else:
                args = args[:2] + (data,) + args[3:]

        return await func(*args, **kwargs)

    return wrapper
