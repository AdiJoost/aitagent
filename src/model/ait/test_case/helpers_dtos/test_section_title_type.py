from enum import Enum


class TestSectionTitleType(str, Enum):
    STANDARD = "STANDARD"
    TITLE_HEADER_1 = "TITLE_HEADER_1"
    TITLE_HEADER_2 = "TITLE_HEADER_2"
    TITLE_HEADER_3 = "TITLE_HEADER_3"
    TITLE_HEADER_4 = "TITLE_HEADER_4"