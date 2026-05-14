

from src.model.ait.base_dto.base_dto import BaseDTO


class AuxiliaryMeansDTO(BaseDTO):
    name: str | None = None
    pbmNrOrPartNr: str | None = None