# -*- coding: utf-8 -*-

if __import__('typing').TYPE_CHECKING:
    from tinydb import TinyDB
    from aiohttp.client import ClientSession
    from objects.sakuro import Sakuro

    from typing import Optional

db: 'TinyDB'
http: 'Optional[ClientSession]'
client: 'Sakuro'
