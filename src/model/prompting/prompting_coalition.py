from typing import List

from pydantic import BaseModel


class PromptingCoalition(BaseModel):
    ids: List[int]
    coalitionPrompt: str
