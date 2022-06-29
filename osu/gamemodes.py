import functools
from enum import IntEnum
from enum import unique

from cmyui.osu import Mods

__all__ = ("GameMode",)

gm_str = (
    "vn!std",
    "vn!taiko",
    "vn!catch",
    "vn!mania",
    "rx!std",
    "rx!taiko",
    "rx!catch",
    "ap!std",
)


@unique
class GameMode(IntEnum):
    vn_std = 0
    vn_taiko = 1
    vn_catch = 2
    vn_mania = 3

    rx_std = 4
    rx_taiko = 5
    rx_catch = 6

    ap_std = 7

    @classmethod
    @functools.lru_cache(maxsize=32)
    def from_params(cls, mode_vn: int, mods: Mods) -> "GameMode":
        mode = mode_vn
        if mods & Mods.RELAX:
            mode += 4

        elif mods & Mods.AUTOPILOT:
            mode += 7

        if mode > 7:  # don't apply mods if invalid
            return cls(mode_vn)

        return cls(mode)

    @classmethod
    @functools.lru_cache(maxsize=32)
    def from_str(cls, mods: str, mode: str) -> "GameMode":
        gm = f"{mods}!{mode}"

        return cls(gm_str.index(gm))

    @functools.cached_property
    def as_vanilla(self) -> int:
        if self.value == self.ap_std:
            return 0

        return self.value % 4

    @functools.cache
    def __repr__(self) -> str:
        return gm_str[self.value]
