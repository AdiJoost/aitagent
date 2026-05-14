from enum import Enum


class InspectionType(str, Enum):
    FULL_AND_PARTIAL_TEST = "FULL_AND_PARTIAL_TEST"
    FULL_TEST_ONLY = "FULL_TEST_ONLY"