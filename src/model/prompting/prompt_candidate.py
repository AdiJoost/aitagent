from pydantic import BaseModel


class PromptCandidate(BaseModel):
    id: int
    name: str
    abbreviation: str
    prompt: str
