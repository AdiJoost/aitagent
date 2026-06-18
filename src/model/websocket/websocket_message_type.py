from enum import Enum


class WebSocketMessageType(str, Enum):
    ERROR = "ERROR"
    START = "START"
    THINKING = "THINKING"
    USER_MESSAGE = "USER_MESSAGE"
    DONE = "DONE"
    CANCEL = "CANCEL"
