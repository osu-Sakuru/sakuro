import traceback
from datetime import datetime
from functools import wraps
from sys import exc_info

from cmyui import Ansi, log
from discord import Embed

from utils.user import UserHelper


def handle_exception(func) -> wraps:
    """Simple exception handler for commands."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except:
            err = exc_info()
            tb = ''.join(traceback.format_tb(err[2]))
            log(f"Unknown error occurred: {err[1]}\n{tb}", Ansi.RED)
            return await args[1].send(f"Error occurred while executing this command: `{err[1]}`\n```sh\n{tb}\n```")

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
    """Simple wrapper for command that's requires user be linked."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = args[2]
        ctx = args[1]

        if user is None:
            if not (data := await UserHelper.getDiscordUser(ctx.message.author.id)):
                embed = Embed(title="Notice!",
                              description="Your account should be linked with our bot to use this command. " +
                              "Please, follow [this link](https://sakuru.pw/settings/socials) to link your account.",
                              timestamp=datetime.now(), colour=0xeaff00)
                embed.set_footer(text='Sakuru.pw private osu! server.')

                return await ctx.send(embed=embed)
            else:
                upd_args = list(args)
                upd_args[2] = data['osu_name']
                args = tuple(upd_args)
        else:
            if not await UserHelper.getOsuUserByName(user, "info"):
                return await ctx.send(f"User `{user}` not found or didn't exists.")

        return await func(*args, **kwargs)

    return wrapper
