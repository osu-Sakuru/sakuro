# -*- coding: utf-8 -*-
from typing import Optional, Any, Union

from objects import glob, config

BASE_URL = "https://api.sakuru.pw"

class UserHelper:
    def __init__(self):
        pass

    @classmethod
    async def getDiscordUser(cls, discord_id: int) -> Optional[dict]:
        async with glob.http.get(f"{BASE_URL}/get_player_bydiscord", params={
            'id': discord_id,
            'secret': config.API_SECRET
        }) as resp:
            if resp.status == 200:
                return (await resp.json())['player']
            else:
                return None

    @classmethod
    async def getOsuUserByName(cls, osu_name: str, scope: str) -> Optional[dict[Any, Any]]:
        async with glob.http.get(f"{BASE_URL}/get_player_info", params={
            'name': osu_name,
            'scope': scope
        }) as resp:
            if resp.status == 200:
                data = await resp.json()

                if scope == "all":
                    return data['player']
                else:
                    return data['player'][scope]
            else:
                return None

    @classmethod
    async def getOsuUserById(cls, osu_id: int, scope: str) -> Optional[dict]:
        async with glob.http.get(f"{BASE_URL}/get_player_info", params={
            'id': osu_id,
            'scope': scope
        }) as resp:
            if resp.status == 200:
                data = await resp.json()

                if scope == "all":
                    return data['player']
                else:
                    return data['player'][scope]
            else:
                return None

    @classmethod
    async def getUserScores(cls, user: Union[int, str], mode: int, table: str, limit: int, scope: str = None,
                            bm: Union[int, str] = None):
        params = {
            'table': table,
            'limit': limit,
            'mode': mode
        }

        if type(user) == int:
            params.update({'id': user})
        else:
            params.update({'name': user})

        if scope:
            params.update({'scope': scope})

        if bm:
            params.update({'bm': bm})

        async with glob.http.get(f"{BASE_URL}/get_player_scores", params=params) as resp:
            if resp.status == 200:
                data = await resp.json()

                return data['scores']
            else:
                return None
