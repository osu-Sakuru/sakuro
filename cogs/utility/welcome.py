# -*- coding: utf-8 -*-

from datetime import datetime

from cmyui import log, Ansi
from discord import Member, Embed
from discord.ext import commands

from objects import config
from objects.sakuro import Sakuro


class WelcomeCog(commands.Cog):
    def __init__(self, bot: Sakuro):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        if member.guild.id == config.SAKURU_ID:
            channel = member.guild.system_channel

            embed = Embed(title="Hey hey! New player has arrived!",
                          description=f"Welcome to Sakuru.pw discord server {member.mention}! " +
                                      "Hope you enjoy it here and be Happy! If you want use Sakuro " +
                                      "please, follow [this link](https://sakuru.pw/settings/socials) to link your account.",
                          timestamp=datetime.now(),
                          colour=0xeaff00)

            embed.set_thumbnail(url="https://sakuru.pw/static/ingame.png")
            embed.set_footer(text='Sakuru.pw private osu! server.')

            await channel.send(embed=embed)

def setup(bot) -> None:
    log(f"Initiated {__name__} cog!", Ansi.CYAN)
    bot.add_cog(WelcomeCog(bot))
