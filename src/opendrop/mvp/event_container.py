from enum import IntEnum


class MouseMoveEvent:
    # Timestamp of the event
    timestamp = None  # type: Optional[float]

    # Position of the cursor
    pos = None  # type: Optional[Tuple[int, int]]

    # Modifier bitfield
    state = None  # type: Optional[ModifierType]

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class ModifierType(IntEnum):
    SHIFT = 1
    CAPSLOCK = 2
    CONTROL = 4
    ALT = 8
    BUTTON1 = 16
    BUTTON2 = 32
    BUTTON3 = 64
