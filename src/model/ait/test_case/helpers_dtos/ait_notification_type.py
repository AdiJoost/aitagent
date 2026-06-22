from enum import Enum


class AitNotificationType(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    NUMBERREQUEST = "NUMBERREQUEST"
    STRINGREQUEST = "STRINGREQUEST"
    FAILURE = "FAILURE"