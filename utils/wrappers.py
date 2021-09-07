from datetime import datetime
from functools import wraps

from discord import Embed

from objects.sakuro import CommandWrap
from objects.user import UserHelper
from utils.misc import sakuro_error


def check_args(func) -> wraps:
    """Simple argument checker for commands."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Getting required arguments, skip username
        ctx, _, mods, mode = args[1:5]

        if mods.startswith('-'):
            mods = mods.replace('-', '')
            mode = mode.replace('-', '')
            args = args[:3] + (mods, mode) + args[5:]

        if mods not in ('vn', 'rx', 'ap'):
            return await ctx.send('Invalid mods provided! (vn, rx, ap)')

        if mode not in ('std', 'mania', 'taiko'):
            return await ctx.send('Invalid mode provided! (std, mania, taiko)')

        if mode == 'mania':
            if mods != 'vn':
                return await ctx.send('Invalid mods for mania! Only vn is allowed.')
        elif mode == 'taiko':
            if mods not in ('vn', 'rx'):
                return await ctx.send('Invalid mods for taiko! Only vn and rx is allowed.')

        return await func(*args, **kwargs)

    return wrapper

def sakuroCommand(name=None, cls=None, **attrs):
    """Custom command wrapper for Sakuro."""
    if cls is None:
        cls = CommandWrap

    def decorator(func):
        if isinstance(func, CommandWrap):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator

def link_required(func) -> wraps:
    """Simple wrapper for command that's requires user be linked. NOTE: Use it ONLY with commands."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        name = args[2]
        ctx = args[1]

        if name is None or name.startswith('-'):
            if not (data := await UserHelper.getDiscordUser(ctx.message.author.id)):
                embed = Embed(title="Notice!",
                              description="Your account should be linked with our bot to use this command. " +
                                          "Please, follow [this link](https://sakuru.pw/settings/socials) to link your account.",
                              timestamp=datetime.now(), color=0xeaff00)
                embed.set_footer(text='Sakuru.pw private osu! server.')

                return await ctx.send(embed=embed)
            else:
                if name is not None and name.startswith('-'):
                    args = args[:2] + (data, name) + args[4:]
                else:
                    args = args[:2] + (data,) + args[3:]
        else:
            if not (data := await UserHelper.getOsuUserByName(name, "info")):
                return await ctx.send(embed=sakuro_error(
                    title=f"Something went wrong!",
                    error=f"User `{name}` not found or didn't exists.",
                    color=ctx.author.color
                ))
            else:
                args = args[:2] + (data,) + args[3:]

        return await func(*args, **kwargs)

    return wrapper
