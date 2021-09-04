# -*- coding: utf-8 -*-
from typing import Optional

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
