from enum import Enum


class ChangeType(str, Enum):
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    ADD = "ADD"