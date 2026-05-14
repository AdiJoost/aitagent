from enum import Enum


class State(str, Enum):
    ENABLED = "ENABLED",
    DISABLED = "DISABLED"
    HIDDEN = "HIDDEN"
