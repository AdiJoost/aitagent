from pydantic import BaseModel

class BaseDTO(BaseModel):
    dbId: int | None = None