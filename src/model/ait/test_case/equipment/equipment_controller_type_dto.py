
from pydantic import BaseModel


class EquipmentControllerTypeDTO(BaseModel):
    type: str | None = None
    displayName: str | None = None