# -*- coding: utf-8 -*-

import os
import pathlib
import sys

from cmyui.osu.oppai_ng import OppaiWrapper
from typing import Optional, Union

import aiofiles

from utils import glob

class Calculator:
    def __init__(self) -> None:
        pass

    @classmethod
    async def getOsuFile(cls: 'Calculator', beatmap_id: int) -> Union[bool, pathlib.Path]:
        path = pathlib.Path(f"{os.getcwd()}/osu/beatmaps/{beatmap_id}.osu")

        if not path.is_file():
            async with glob.http.get(f"https://osu.ppy.sh/osu/{beatmap_id}") as resp:
                if resp.status == 200:
                    data = await resp.read()
                else:
                    return False

                path.write_bytes(data)
                return path
        else:
            return path

    @classmethod
    async def calculate(cls: 'Calculator', beatmap_id: int,
                        mode: int = 0, mods: int = None, acc: float = None,
                        combo: int = None, miss: int = None, score: int = None) -> ['Calculator']:
        beatmap_file = pathlib.Path(f"{os.getcwd()}/osu/beatmaps/{beatmap_id}.osu")
        oppai_path = pathlib.Path(os.getcwd())

        # TODO: Windows support? [WinError 193] %1 is not a valid Win32 application
        if sys.platform.startswith('win'):
            oppai_path = oppai_path / "oppai.exe"
        else:
            oppai_path = oppai_path / "liboppai.so"

        if not beatmap_file.is_file():
            beatmap_file = await cls.getOsuFile(beatmap_id)

        if mode in (0, 1):
            with OppaiWrapper(str(oppai_path)) as ezpp:
                if mods:
                    ezpp.set_mods(mods)
                if acc:
                    ezpp.set_accuracy_percent(acc)
                if combo:
                    ezpp.set_combo(combo)
                if miss:
                    ezpp.set_nmiss(miss)

                ezpp.calculate(beatmap_file)

                return {
                    'map_id': beatmap_id,
                    'pp': ezpp.get_pp(),
                    'stars': ezpp.get_sr(),
                    'map_creator': str(ezpp.get_creator(), 'utf-8'),
                    'map_fullname': f"{str(ezpp.get_artist(), 'utf-8')} - {str(ezpp.get_title(), 'utf-8')} [{str(ezpp.get_version(), 'utf-8')}]"
                }
        elif mode == 2:
            return cls
        else:
            return cls
