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
        self.map_id: Optional[int] = 0

        self.pp: Optional[float] = 0.0
        self.stars: Optional[float] = 0.0
        self.mods: Optional[int] = 0

        self.map_creator: Optional[str] = ""
        self.map_fullname: Optional[str] = ""

    @property
    def as_dict(self) -> dict[str]:
        return {
            'map_id': self.map_id,
            'pp': self.pp,
            'stars': self.stars,
            'map_creator': self.map_creator,
            'map_fullname': self.map_fullname
        }

    @classmethod
    async def getOsuFile(cls: 'Calculator', beatmap_id: int) -> Union[bool, pathlib.Path]:
        path = pathlib.Path(f"{os.getcwd()}/osu/beatmaps/{beatmap_id}.osu")

        if not path.is_file():
            async with glob.http.get(f"https://osu.ppy.sh/osu/{beatmap_id}") as resp:
                if resp.status == 200:
                    data = await resp.read()
                else:
                    return False

            async with aiofiles.open(
                    path, "wb"
            ) as outfile:
                await outfile.write(data)
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

                ret = cls

                ret.map_id = beatmap_id
                ret.pp = ezpp.get_pp()
                ret.mods = ezpp.get_mods()
                ret.stars = ezpp.get_sr()
                ret.map_fullname = f"{ezpp.get_artist()} - {ezpp.get_title()} [{ezpp.get_version()}]"
                ret.map_creator = ezpp.get_creator()

                return ret
        elif mode == 2:
            return cls
        else:
            return cls
