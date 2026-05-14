from datetime import datetime

from src.model.ait.base_dto.base_dto import BaseDTO
from src.model.ait.test_case.equipment.equipment_type_dto import EquipmentTypeDTO
from src.model.ait.test_case.helpers_dtos.state import State
from src.model.ait.test_case.parameter.parameter_value_dto import ParameterValueDTO


class EquipmentDTO(BaseDTO):
    equipmentTypeDto: EquipmentTypeDTO | None = None
    serialNr: str | None = None
    state: State | None = None
    description: str | None = None
    pbmNr: str | None = None
    ipAddress: str | None = None
    portNr: int | None = None
    createDate: datetime | None = None
    changeDate: datetime | None = None
    equipmentId: int | None = None
    areaDbId: int | None = None
    parameters: list[ParameterValueDTO] | None = None