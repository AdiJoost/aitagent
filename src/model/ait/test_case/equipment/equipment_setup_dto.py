from src.model.ait.base_dto.base_dto import BaseDTO
from src.model.ait.test_case.equipment.equipment_type_dto import EquipmentTypeDTO


class EquipmentSetupDTO(BaseDTO):
    equipmentTypeDTO: EquipmentTypeDTO | None = None
    equipmentDesignator: str | None = None