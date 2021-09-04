# -*- coding: utf-8 -*-

if __import__('typing').TYPE_CHECKING:
    from tinydb import TinyDB
    from aiohttp.client import ClientSession
    from discord.ext.commands import Bot

    from typing import Optional

db: 'TinyDB'
http: 'Optional[ClientSession]'
client: 'Bot'
start_time: int
donors: dict[str, any]
