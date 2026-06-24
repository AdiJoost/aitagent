from enum import Enum


class LoopStopReason(str, Enum):
    CODEWORD_DETECTED = "CODEWORD_DETECTED"
    LOOP_EXPIRED = "LOOP_EXPIRED"
