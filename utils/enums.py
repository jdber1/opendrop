from enum import Enum

class FunctionType(Enum):
    PENDANT_DROP = "Pendant Drop"
    CONTACT_ANGLE = "Contact Angle"

class Stage(Enum):
    ACQUISITION = 1
    PREPARATION = 2
    ANALYSIS = 3
    OUTPUT = 4

class Move(Enum):
    Next = 1
    Back = -1