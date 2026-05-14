

from typing import List

from pydantic import BaseModel

from src.model.evaluation_dto.subclasses.section_update_dto import SectionUpdateDTO
from src.model.evaluation_dto.subclasses.test_element_update_dto import TestElementUpdateDTO



class UpdateDTOList(BaseModel):
    testSectionsUpdates: List[SectionUpdateDTO] | None = None
    testElementSectionUpdates: List[TestElementUpdateDTO] | None = None