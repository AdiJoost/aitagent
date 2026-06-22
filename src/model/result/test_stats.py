from pydantic import BaseModel

from src.model.result.metrics.metrics_dto import MetricsDTO


class TestStats(BaseModel):
    prior: MetricsDTO
    posterior: MetricsDTO
    sectionsToDelete: int
    sectionWithUpdates: int
