from src.model.ait.base_dto.base_dto import BaseDTO
from src.model.ait.test_case.equipment.equipment_controller_type_dto import EquipmentControllerTypeDTO


class EquipmentTypeDTO(BaseDTO):
    name: str | None = None
    pbmGroup: str | None = None
    equipmentControllerType: EquipmentControllerTypeDTO | None = None
    hasIp: bool | None = None
    multipleAssignments: bool | None = None