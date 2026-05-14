from datetime import datetime
from enum import Enum
from pydantic import BaseModel

from src.model.ait.base_dto.base_dto import BaseDTO
from src.model.ait.test_case.auxiliary_means_dto import AuxiliaryMeansDTO
from src.model.ait.test_case.helpers_dtos.inspection_type import InspectionType
from src.model.ait.test_case.helpers_dtos.state import State
from src.model.ait.test_case.parameter.parameter_value_dto import ParameterValueDTO
from src.model.ait.test_case.test_section_dto import TestSectionDTO
from src.model.ait.test_case.equipment.workstation_setup_dto import WorkstationSetupDTO
from src.model.ait.test_case.equipment.workstationless_equipment_setup_dto import WorkstationlessEquipmentSetupDTO





class TestCaseBaseDTO(BaseDTO):
    released: bool | None = None
    revisionNr: int | None = None
    testCaseId: int | None = None
    title: str | None = None
    inspectionType: InspectionType | None = None
    areaDbId: int | None = None

class TestCaseDTO(TestCaseBaseDTO):
    createDate: datetime | None = None
    changeDate: datetime | None = None
    creator: str | None = None
    lockedBy: str | None = None
    testProcedure: str | None = None
    references: str | None = None
    state: State | None = None
    testRequirements: str | None = None
    testSectionDTOList: list[TestSectionDTO] | None = None
    toolNr: str | None = None
    workstationSetupDto: WorkstationSetupDTO | None = None
    isAutomatic: bool | None = None
    auxiliaryMeansList: list[AuxiliaryMeansDTO] | None = None
    parameters: list[ParameterValueDTO] | None = None
    traceNumber: str | None = None
    workstationlessEquipmentSetupDtoList: list[WorkstationlessEquipmentSetupDTO] | None = None

