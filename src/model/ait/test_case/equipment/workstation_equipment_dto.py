from pydantic import BaseModel

from src.model.ait.test_case.equipment.equipment_dto import EquipmentDTO


class WorkstationEquipmentDTO(BaseModel):
    equipmentDesignator: set | None = None
    equipment: EquipmentDTO | None = None