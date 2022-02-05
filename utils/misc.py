# -*- coding: utf-8 -*-
from enum import IntEnum, unique
import re
from datetime import datetime
from random import choice
from typing import Optional

from discord import Embed
from discord.components import C

from objects import config

CHO_BEATMAP_REGEX = re.compile(r'^https://osu\.ppy\.sh/beatmapsets/(?P<sid>\d{1,10})#/?(?P<mode>:?osu|taiko|fruits|mania)?/(?P<bid>\d{1,10})/?$')
SAKURU_BEATMAP_REGEX = re.compile(r'^https://sakuru\.pw/b/(?P<bid>\d{1,10})')

_win_cond_str = (
    'Score',
    'Accuracy',
    'Combo',
    'ScoreV2'
)

_team_types_str = (
    'Head To Head',
    'TAG Coop',
    'TeamVS',
    'TAG TeamVS'
)

def convert_mode_int(mode: str) -> Optional[int]:
    """Converts mode (str) to mode (int)."""
    if mode not in _str_mode_dict:
        print('invalid mode passed into utils.convert_mode_int?')
        return
    return _str_mode_dict[mode]

_str_mode_dict = {
    'std': 0,
    'taiko': 1,
    'catch': 2,
    'mania': 3
}

def convert_mode_str(mode: int) -> Optional[str]:
    """Converts mode (int) to mode (str)."""
    if mode not in _mode_str_dict:
        print('invalid mode passed into utils.convert_mode_str?')
        return
    return _mode_str_dict[mode]

_mode_str_dict = {
    0: 'std',
    1: 'taiko',
    2: 'catch',
    3: 'mania'
}

def convert_grade_emoji(grade: str) -> Optional[str]:
    """Converts grade to emoji."""
    if grade not in _grade_emoji_dict:
        print('invalid mode passed into utils.convert_grade_emoji?')
        return
    return _grade_emoji_dict[grade]

_grade_emoji_dict = {
    'F': '<:rankF:811387747158720592>',
    'D': '<:rankD:811387785818275871>',
    'C': '<:rankC:811387822472560640>',
    'B': '<:rankB:811387834307969065>',
    'A': '<:rankA:811387847940243526>',
    'S': '<:rankS:811387863982669824>',
    'X': '<:rankX:811387875706011648>',
    'SH': '<:rankSH:811387887832662056>',
    'XH': '<:rankXH:811387902545494056>'
}

def get_completion(elapsed: int, total: int) -> float:
    return round(elapsed / (total * 1000) * 100, 2)

def make_safe_name(name: str) -> str:
    """Return a name safe for usage in sql."""
    return name.lower().replace(' ', '_')

def _get_required_score_for_level(level: int) -> float:
    if level <= 100:
        if level > 1:
            return round(5000 / 3 * (4 * pow(level, 3) - 3 * pow(level, 2) - level) + round(1.25 * pow(1.8, level - 60)))
        else:
            return 1
    else:
        return 26931190829 + 100000000000 * (level - 100)

def get_level(score: int) -> int:
    level = 1

    while True:
        required_score = _get_required_score_for_level(level)

        if score < required_score:
            return level - 1
        else:
            level += 1

def get_level_percent(score: int, base_level: int) -> float:
    # division by zero
    base_level = 1 if base_level < 1 else base_level

    base_levelscore = _get_required_score_for_level(base_level)
    score_progress = score - base_levelscore
    difference = _get_required_score_for_level(base_level + 1) - base_levelscore

    return score_progress / difference * 100

def sakuru_only(ctx) -> bool:
    return ctx.guild.id == config.SAKURU_ID

def sakuro_error(error: str, title: str, color: any) -> Embed:
    ret = Embed(title=title,
                description=error,
                color=color,
                timestamp=datetime.now())

    ret.set_thumbnail(url=choice(config.ERROR_GIFS))
    ret.set_footer(text=choice(config.WORDS))

    return ret

def convert_status_str(status: int) -> str:
    if status == 0:
        ret = "🪦 Unranked"
    elif status == 2:
        ret = "⭐ Ranked"
    elif status == 3:
        ret = "✔️ Approved"
    elif status == 4:
        ret = "🆗 Qualified"
    elif status == 5:
        ret = "❤️ Loved"
    else:
        ret = "Unknown status"

    return ret

def convert_str_status(status: str) -> int:
    if status == "rank":
        ret = 2
    elif status == "unrank":
        ret = 0
    elif status == "love":
        ret = 5
    else:
        ret = -1

    return ret

_actions = {
    'player_join': '🙋‍♂️ `{}` joined lobby.',
    'update_teamtype': '❗ Updated match type from `{}` to `{}`.',
    'update_condition': '🧑‍🦽 Updated win condition from `{}` to `{}`.',
    'player_left': '🚶‍♂️ `{}` left lobby.',
    'update_freemods': '🆓 Updated freemods from `{}` to `{}`'
}

def parse_history(action: str, old_value: Optional[str], new_value: str, users: dict[int, str]) -> str:
    if old_value is None:
       return _actions[action].format(users[int(new_value)]['name'])
    else:
        # match action:
        #     case "update_teamtype":
        #         return _actions[action].format(_team_types_str[int(old_value)], _team_types_str[int(new_value)])
        #     case "update_condition":
        #         return _actions[action].format(_win_cond_str[int(old_value)], _win_cond_str[int(new_value)])
        #     case "update_freemods":
        #         return _actions[action].format(
        #             "Enabled" if old_value == "1" else "Disabled", 
        #             "Enabled" if new_value == "1" else "Disabled"
        #         )
        #     case _:
        #         return "Wrong action."
        ...
