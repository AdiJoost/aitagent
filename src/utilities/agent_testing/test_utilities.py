import json
import os
from itertools import combinations
from pathlib import Path
from typing import List

from src.model.prompting.prompt_candidate import PromptCandidate
from src.model.prompting.prompting_coalition import PromptingCoalition
from src.model.result.metrics.posterior_dto import PosteriorMetrics
from src.model.result.result import ResultDTO
from src.model.result.test_stats import TestStats


def getPromptingStrategies(filePath: Path) -> List[PromptCandidate]:
    if os.path.isfile(filePath):
        with open(filePath, "r") as file:
            data = json.load(file)
        return [PromptCandidate(**item) for item in data]
    return []


def getPromptingMatrix(
    promptingCandidates: List[PromptCandidate],
) -> List[PromptingCoalition]:
    permutation_matrix = [
        PromptingCoalition(ids=[], coalitionPrompt=""),
    ]
    for size in range(1, len(promptingCandidates) + 1):
        for subset in combinations(promptingCandidates, size):
            coalition = PromptingCoalition(
                ids=[p.id for p in subset],
                coalitionPrompt=" ".join(p.prompt for p in subset),
            )
            permutation_matrix.append(coalition)
    return permutation_matrix


def createOrExtendResult(
    results: TestStats, coalition: PromptingCoalition, resultpath: Path
):
    if not os.path.exists(resultpath):
        result = ResultDTO(prior=results.prior, updated=[])
        resultpath.parent.mkdir(parents=True, exist_ok=True)
        with open(resultpath, "w") as file:
            file.write(result.model_dump_json(indent=2))
    with open(resultpath, "r") as file:
        result = ResultDTO.model_validate_json(file.read())
    updatedResult = PosteriorMetrics(metrics=results.posterior, coalition=coalition)
    result.updated.append(updatedResult)
    with open(resultpath, "w") as file:
        file.write(result.model_dump_json(indent=2))
