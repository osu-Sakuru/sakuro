# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Union

from cmyui import log, Ansi
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Context

from utils.user import UserHelper
from utils.wrappers import handle_exception, link_required, check_args


class OsuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @handle_exception
    @check_args
    @link_required
    async def osu(self, ctx: Context, player: Union[dict, str] = None, mods: str = 'vn', mode: str = 'std'):
        scope = await UserHelper.getOsuUserByName(player['name'], scope="all")

        # TODO: Need to fix api response;
        # embed = Embed(description=f"**▸ Official Rank:** #{player['stats'][f'rank_{mods}_{mode}']} " +
        #                           f"({player['info']['country'].upper()}#{player['stats'][f'crank_{mods}_{mode}']})\n**▸ " +
        #                           f"Level:** `not implemented`\n**▸ Total PP:** {player['stats'][f'pp_{mods}_{mode}']}\n**▸ " +
        #                           f"Hit Accuracy:** {player['stats'][f'acc_{mods}_{mode}']}%\n**▸ " +
        #                           f"Playcount:** {player['stats'][f'plays_{mods}_{mode}']}", timestamp=datetime.now(), colour=0x00ff00)

        embed = Embed(description=f"**▸ Official Rank:** #{scope['stats'][f'rank_{mods}_{mode}']} " +
                                  f"({scope['info']['country'].upper()}#{scope['stats'][f'crank_{mods}_{mode}']})\n**▸ " +
                                  f"Level:** `not implemented`\n**▸ Total PP:** {scope['stats']['pp']}\n**▸ " +
                                  f"Hit Accuracy:** {scope['stats']['acc']:.2f}%\n**▸ " +
                                  f"Playcount:** {scope['stats']['plays']}", timestamp=datetime.now(), colour=0x00ff00)

        embed.set_author(name=f"{mode.upper()}!{mods.upper()} Profile for {player['name']}",
                         icon_url=f"https://sakuru.pw/static/flags/{scope['info']['country'].upper()}.png",
                         url=f"https://sakuru.pw/u/{scope['info']['id']}")

        embed.set_thumbnail(url=f"https://a.sakuru.pw/{scope['info']['id']}")
        embed.set_footer(text="On Sakuru.pw server.")

        await ctx.send(embed=embed)

def setup(bot):
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(OsuCog(bot))
