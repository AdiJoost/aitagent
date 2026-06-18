from pydantic import BaseModel

from src.model.ait.test_case.helpers_dtos.test_section_title_type import \
    TestSectionTitleType


class ReducedTestSectionDTO(BaseModel):
    title: str | None = None
    titleType: TestSectionTitleType | None = None
    dbId: int | None = None