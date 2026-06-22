from pydantic import BaseModel

from src.model.result.metrics.accuracy_dto import AccuracyDTO


class MetricsDTO(BaseModel):
    titleType: AccuracyDTO
    title: AccuracyDTO
    deletion: AccuracyDTO
    invalidTransitionRate: float = 0
    totalSections: int