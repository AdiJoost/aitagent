from src.model.ait.base_dto.base_dto import BaseDTO


class ElementTagDTO(BaseDTO):
    tagId: int | None = None
    partNames: list[str] | None = None
    description: str | None = None
    areaDbid: int | None = None