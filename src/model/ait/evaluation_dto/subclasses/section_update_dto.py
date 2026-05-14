from pydantic import BaseModel

from src.model.ait.evaluation_dto.subclasses.change_type import ChangeType
from src.model.ait.test_case.test_section_dto import TestSectionDTO


class SectionUpdateDTO(BaseModel):
    sectionId: int | None = None
    changeType: ChangeType | None = None
    sectionDTO: TestSectionDTO | None = None