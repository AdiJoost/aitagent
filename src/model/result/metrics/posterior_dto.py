from pydantic import BaseModel

from src.model.prompting.prompting_coalition import PromptingCoalition
from src.model.result.metrics.metrics_dto import MetricsDTO


class PosteriorMetrics(BaseModel):
    metrics: MetricsDTO
    coalition: PromptingCoalition
