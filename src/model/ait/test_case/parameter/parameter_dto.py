from src.model.ait.base_dto.base_dto import BaseDTO
from src.model.ait.test_case.parameter.parameter_type import ParameterType


class ParameterDTO(BaseDTO):
    name: str | None = None
    type: ParameterType | None = None
    unit: str | None = None
    factor: int | None = None
    description: int | None = None