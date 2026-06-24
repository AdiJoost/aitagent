from pydantic import BaseModel

from src.model.prompting.prompting_coalition import PromptingCoalition
from src.model.result.enums.loop_stop_reason import LoopStopReason
from src.model.result.metrics.metrics_dto import MetricsDTO


class PosteriorMetrics(BaseModel):
    metrics: MetricsDTO
    coalition: PromptingCoalition
    executionTime: float | None = 0
    numberOfRounds: int | None = 0
    loopStopReason: LoopStopReason | None = None
