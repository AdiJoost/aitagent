from pydantic import BaseModel

from src.model.ait.test_case.parameter.parameter_dto import ParameterDTO

class ParameterValueDTO(BaseModel):
    rawValue: str | None = None
    parameter: ParameterDTO | None = None