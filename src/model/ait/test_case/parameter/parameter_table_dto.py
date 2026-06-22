from pydantic import BaseModel

from src.model.ait.test_case.parameter.parameter_dto import ParameterDTO
from src.model.ait.test_case.parameter.parameter_row_dto import ParameterRowDTO


class ParameterTableDTO(BaseModel):
    parameters: list[ParameterDTO] | None = None
    rows: list[ParameterRowDTO] | None = None