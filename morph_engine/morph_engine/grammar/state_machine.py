from enum import Enum


class GrammarState(Enum):
    START = "start"
    GROW = "grow"
    CLOSE = "close"
    END = "end"
