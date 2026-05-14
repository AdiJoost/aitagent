from datetime import datetime

from src.model.ait.base_dto.base_dto import BaseDTO
from src.model.ait.test_case.equipment.equipment_setup_dto import EquipmentSetupDTO
from src.model.ait.test_case.equipment.workstation_equipment_dto import WorkstationEquipmentDTO
from src.model.ait.test_case.helpers_dtos.state import State


class WorkstationBaseDTO(BaseDTO):
    type: str | None = None
    equipmentSetupList: list[EquipmentSetupDTO] | None = None

class WorkstationDTO(WorkstationBaseDTO):
    createDate: datetime | None = None
    changeDate: datetime | None = None
    isValid: bool | None = None
    name: str | None = None
    creator: str | None = None
    lastChangedBy: str | None = None
    state: State | None = None
    printer: str | None = None
    workstationSetupDbId: int | None = None
    workstationEquipmentList: list[WorkstationEquipmentDTO] | None = None