<<<<<<< HEAD
import json
import os
from itertools import combinations
from pathlib import Path
from typing import List

from mcp.types import CallToolResult

from src.model.ait.test_case.reduced_test_case_dto import ReducedTestCaseDTO
from src.model.ait.test_case.reduced_test_section_dto import ReducedTestSectionDTO
from src.model.ait.test_case.test_case_dto import TestCaseDTO
from src.model.ait.test_case.test_section_dto import TestSectionDTO
from src.model.prompting.prompt_candidate import PromptCandidate
from src.model.prompting.prompting_coalition import PromptingCoalition
from src.model.result.enums.loop_stop_reason import LoopStopReason
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
    results: TestStats,
    coalition: PromptingCoalition,
    resultpath: Path,
    executionTime: int,
    numberOfRounds: int,
    loopStopReason: LoopStopReason,
):
    if not os.path.exists(resultpath):
        result = ResultDTO(prior=results.prior, results=[])
        resultpath.parent.mkdir(parents=True, exist_ok=True)
        with open(resultpath, "w") as file:
            file.write(result.model_dump_json(indent=2))
    with open(resultpath, "r") as file:
        result = ResultDTO.model_validate_json(file.read())
    updatedResult = PosteriorMetrics(
        metrics=results.posterior,
        coalition=coalition,
        executionTime=executionTime,
        numberOfRounds=numberOfRounds,
        loopStopReason=loopStopReason,
    )
    result.results.append(updatedResult)
    with open(resultpath, "w") as file:
        file.write(result.model_dump_json(indent=2))


def getReducedTestcaseFromCall(message: CallToolResult) -> ReducedTestCaseDTO:
    if message and len(message.content) > 0:
        testCaseDTO = TestCaseDTO.model_validate_json(message.content[0].text)
        return _reduceTestcase(testCaseDTO=testCaseDTO)
    return "TestCaseDTO not found. Use the MCP to get the current testcase"


def _reduceTestcase(testCaseDTO: TestCaseDTO) -> str:
    testSectionDTOList = []
    for testSectionDTO in testCaseDTO.testSectionDTOList:
        newTestSection = ReducedTestSectionDTO(
            title=testSectionDTO.title,
            titleType=testSectionDTO.titleType,
            dbId=testSectionDTO.dbId,
        )
        testSectionDTOList.append(newTestSection)

    reducedTestCaseDTO = ReducedTestCaseDTO(
        testSectionDTOList=testSectionDTOList, title=testCaseDTO.title
    )
    return reducedTestCaseDTO.model_dump_json(indent=2)
=======
import json
import os
from itertools import combinations
from pathlib import Path
from typing import List

from mcp.types import CallToolResult

from src.model.ait.test_case.reduced_test_case_dto import ReducedTestCaseDTO
from src.model.ait.test_case.reduced_test_section_dto import ReducedTestSectionDTO
from src.model.ait.test_case.test_case_dto import TestCaseDTO
from src.model.ait.test_case.test_section_dto import TestSectionDTO
from src.model.prompting.prompt_candidate import PromptCandidate
from src.model.prompting.prompting_coalition import PromptingCoalition
from src.model.result.enums.loop_stop_reason import LoopStopReason
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
    results: TestStats,
    coalition: PromptingCoalition,
    resultpath: Path,
    executionTime: int,
    numberOfRounds: int,
    loopStopReason: LoopStopReason,
):
    if not os.path.exists(resultpath):
        result = ResultDTO(prior=results.prior, results=[])
        resultpath.parent.mkdir(parents=True, exist_ok=True)
        with open(resultpath, "w") as file:
            file.write(result.model_dump_json(indent=2))
    with open(resultpath, "r") as file:
        result = ResultDTO.model_validate_json(file.read())
    updatedResult = PosteriorMetrics(
        metrics=results.posterior,
        coalition=coalition,
        executionTime=executionTime,
        numberOfRounds=numberOfRounds,
        loopStopReason=loopStopReason,
    )
    result.results.append(updatedResult)
    with open(resultpath, "w") as file:
        file.write(result.model_dump_json(indent=2))


def getReducedTestcaseFromCall(message: CallToolResult) -> ReducedTestCaseDTO:
    if message and len(message.content) > 0:
        testCaseDTO = TestCaseDTO.model_validate_json(message.content[0].text)
        return _reduceTestcase(testCaseDTO=testCaseDTO)
    return "TestCaseDTO not found. Use the MCP to get the current testcase"


def _reduceTestcase(testCaseDTO: TestCaseDTO) -> str:
    testSectionDTOList = []
    for testSectionDTO in testCaseDTO.testSectionDTOList:
        newTestSection = ReducedTestSectionDTO(
            title=testSectionDTO.title,
            titleType=testSectionDTO.titleType,
            dbId=testSectionDTO.dbId,
        )
        testSectionDTOList.append(newTestSection)

    reducedTestCaseDTO = ReducedTestCaseDTO(
        testSectionDTOList=testSectionDTOList, title=testCaseDTO.title
    )
    return reducedTestCaseDTO.model_dump_json(indent=2)
>>>>>>> ad229f7e9d82747dcf8efd000a412118f5d291e2
