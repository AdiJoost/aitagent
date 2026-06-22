from pydantic import BaseModel

from src.model.ait.test_case.reduced_test_section_dto import \
    ReducedTestSectionDTO
from src.model.ait.test_case.test_section_dto import TestSectionDTO


class ReducedTestCaseDTO(BaseModel):
    testSectionDTOList: list[ReducedTestSectionDTO] | None = None
    title: str | None = None