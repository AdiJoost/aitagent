from pydantic import BaseModel

from src.model.result.metrics.confusion_matrix import ConfusionMatrix


class AccuracyDTO(BaseModel):
    overall: float = 0
    confusion_matrix: ConfusionMatrix
