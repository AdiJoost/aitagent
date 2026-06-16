from typing import List

from pydantic import BaseModel

from src.model.result.metrics.metrics_dto import MetricsDTO
from src.model.result.metrics.posterior_dto import PosteriorMetrics


class ResultDTO(BaseModel):
    prior: MetricsDTO
    results: List[PosteriorMetrics]
