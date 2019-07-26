from enum import IntEnum

from gi.repository import Gdk


class Key(IntEnum):
    UNKNOWN = -1

    Up = Gdk.KEY_Up
    Right = Gdk.KEY_Right
    Down = Gdk.KEY_Down
    Left = Gdk.KEY_Left

    @classmethod
    def from_value(cls, value: int) -> 'Key':
        try:
            return Key(value)
        except ValueError:
            return Key.UNKNOWN


class Modifier:
    SHIFT = int(Gdk.ModifierType.SHIFT_MASK)


class KeyEvent:
    def __init__(self, key: Key, modifier: int):
        self.key = key
        self.modifier = modifier
