from datetime import datetime

from src.model.ait.base_dto.base_dto import BaseDTO
from src.model.ait.test_case.helpers_dtos.inspection_type import InspectionType
from src.model.ait.test_case.helpers_dtos.state import State
from src.model.ait.test_case.helpers_dtos.test_section_title_type import TestSectionTitleType
from src.model.ait.test_case.parameter.parameter_table_dto import ParameterTableDTO
from src.model.ait.test_case.test_element_dto import TestElementDTO

class TestSectionBaseDTO(BaseDTO):
    title: str | None = None
    released: bool | None = None
    inspectionType: InspectionType | None = None

class TestSectionDTO(TestSectionBaseDTO):
    createDate: datetime | None = None
    changeDate: datetime | None = None
    descriptionGerman: str | None = None
    state: State | None = None
    titleType: TestSectionTitleType | None = None
    testElementDTOList: list[TestElementDTO] | None = None
    parameters: ParameterTableDTO | None = None