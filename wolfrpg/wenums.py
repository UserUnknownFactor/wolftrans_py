from enum import IntEnum

class MidiSource(IntEnum):
    HARDWARE = 0
    SOFTWARE = 1
    DISABLED = 2

class VEnable(IntEnum):
    DISABLED = 0
    ENABLED = 1

class InactiveBehavior(IntEnum):
    PAUSE = 0
    RUNNING = 1

class AntiAliasing(IntEnum):
    ENABLED = 0
    DISABLED = 1
    DISABLED_DOUBLE_WIDTH = 2

class ImageScale(IntEnum):
    ROUGH = 0
    SMOOTH = 1

class EncodingType(IntEnum):
    ANSI = 0
    UNICODE = 85

class CharacterMovementWidth(IntEnum):
    SQUARE0_5 = 0
    SQUARE1 = 1

class CharacterAnimationPatterns(IntEnum):
    P3 = 3
    P5 = 5

class CharacterDirections(IntEnum):
    D4 = 4
    D8 = 8

class TileSize(IntEnum):
    T16X16 = 16
    T32X32 = 32
    T40X40 = 40
    T48X48 = 48

class Fps(IntEnum):
    F30 = 30
    F60 = 60

class SpecialFunctionType(IntEnum):
    DISABLED = 0
    LOAD_FROM_FILE = 1
    LOAD_FROM_DATABASE = 2
    MANUAL = 3

class VersionFooter(IntEnum):
    V1 = 193
    V2_2 = 194
    V3_0 = 195
    V3_3 = 196

class Language(IntEnum):
    DEFAULT = 0
    JAPANESE = 1
    HANGUL = 2
    TRADITIONAL_CHINESE = 3
    SIMPLIFIED_CHINESE = 4
    ENGLISH = 5
    WESTERN_EUROPEAN = 6

class Operator(IntEnum):
    GREATER_THAN = 0
    GREATER_OR_EQUAL = 1
    EQUAL = 2
    LESS_OR_EQUAL = 3
    LESS_THAN = 4
    NOT_EQUAL = 5
    BITWISE_AND = 6

class GraphicRenderMode(IntEnum):
    NORMAL = 0
    MULTIPLY = 1
    ADD = 2
    SUBSTRACT = 3

class CharacterAnimation(IntEnum):
    BACK_AND_FORTH = 0
    LOOP = 1

class MoveSpeed(IntEnum):
    SPEED_1X = 4
    SPEED_1_25X = 5
    SPEED_1_5X = 6
    SPEED_1_75X = 7
    SPEED_2X = 8
    CUSTOM = 9

class Frequency(IntEnum):
    EVERY_FRAME = 0
    VERY_SHORT = 1
    SHORT = 2
    MEDIUM = 3
    LONG = 4
    VERY_LONG = 5

class ScreenScale(IntEnum):
    SCALE_1X = 1
    SCALE_2X = 2
    SCALE_3X = 3

class DataIdMethod(IntEnum):
    MANUAL = 0
    SAME_AS_FIRST_STRING_DATA = 1
    SAME_AS_PRECEDING_TYPE_DATA_ID = 2
    FROM_TYPE_IN_DB = 10000