from pydantic import BaseModel


class ParameterRowDTO(BaseModel):
    label: str | None = None
    rawValues: dict[str, str] | None = None