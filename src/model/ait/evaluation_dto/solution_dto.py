

from typing import List

from pydantic import BaseModel

from src.model.ait.evaluation_dto.subclasses.section_update_dto import SectionUpdateDTO
from src.model.ait.evaluation_dto.subclasses.test_element_update_dto import TestElementUpdateDTO


class SolutionDTO(BaseModel):
    testSectionsUpdates: List[SectionUpdateDTO] | None = None
    testElementSectionUpdates: List[TestElementUpdateDTO] | None = None