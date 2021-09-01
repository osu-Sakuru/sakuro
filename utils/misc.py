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
