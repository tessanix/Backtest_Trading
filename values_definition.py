from enum import Enum

class Position(Enum):
    NONE = 1
    LONG = 2
    SHORT = 3

class Trend(Enum):
    NONE = 1
    BULLISH = 2
    BEARISH = 3
