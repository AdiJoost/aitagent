
from pydantic import BaseModel

from src.model.ait.evaluation_dto.subclasses.change_type import ChangeType
from src.model.ait.test_case.test_element_dto import TestElementDTO


class TestElementUpdateDTO(BaseModel):
    elementDbId: int | None = None
    changeType: ChangeType | None = None
    elementDTO: TestElementDTO | None = None