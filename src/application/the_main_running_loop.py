import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from config.loggingSetup import setup_logging
from config.rootPath import getRootPath
from src.llm.agents.manual_agent import ClaudeAgent
from src.llm.agents.ollama_agent import OllamaAgent
from src.model.prompting.prompting_coalition import PromptingCoalition
from src.singel_worker import update_testcase_single_agent
from src.utilities.agent_testing.test_utilities import (
    createOrExtendResult,
    getPromptingMatrix,
    getPromptingStrategies,
)

logger = logging.getLogger(__name__)

evaluating_testcase_name = "test-case-id-126-rev-3-dbid-1989.automate.json"
useAnthropic = False
agentModel = "claude-opus-4-6"


async def the_main_running_loop():
    load_dotenv()
    useAnthropic = os.getenv("USE_ANTHROPIC") == "true"
    agentModel = os.getenv("AGENT_MODEL", "claude-opus-4-6")
    setup_logging()

    mainPath = getRootPath()
    dataPath = mainPath.joinpath("data", "testcases_to_update")
    promptingPaths = mainPath.joinpath("config", "prompt_candidates.json")
    promptingStragegies = getPromptingStrategies(promptingPaths)

    filenames = [f for f in os.listdir(dataPath)]
    for filename in tqdm(filenames, desc="Processing test cases"):
        try:
            filepath = dataPath.joinpath(filename)
            solutionPath = mainPath.joinpath("data", "solutions", filename)
            resultPath = mainPath.joinpath("data", "results", filename[:-5])
            if os.path.isfile(filepath) and os.path.isfile(solutionPath):
                coalitions = getPromptingMatrix(promptingStragegies)
                for coalition in tqdm(coalitions, desc=f"  {filename}", leave=False):
                    try:
                        await _run_manual_agent(
                            filepath,
                            solutionPath,
                            resultpath=resultPath,
                            filename=filename,
                            coalition=coalition,
                        )
                    except Exception as e:
                        logger.exception(
                            f"Error processing coalition in file {filename}. Error: {e}"
                        )
        except Exception as e:
            logger.exception(
                f"Error processing file {filename}, skipping to next. Error: {e}"
            )


async def _run_manual_agent(
    filepath: Path,
    solutionpath: Path,
    resultpath: Path,
    filename: str,
    coalition: PromptingCoalition,
):
    os.makedirs(resultpath, exist_ok=True)
    testCaseString = None
    solutionString = None
    with open(filepath, "r") as file:
        testCaseString = file.read()
    with open(solutionpath, "r") as file:
        solutionString = file.read()
    messages = [
        {
            "role": "system",
            "content": "You are an expert test designer. You modify testcases using MCP tool calls.\n"
            + "IMPORTANT: You MUST use tool calls to interact with the testcase.\n"
            + "Use the appropriate MCP tools to make changes.\n"
            + "Never write code. Always use the provided tool calls. Do not use tools that start with _. Do not provide an explenation, just prompt the tools to execute."
            "When the task is complete, answere with TASK_COMPLETE. Only use ANSWERE_COMPLETE, when you are complete, do not add id in any other instance.",
        },
        {
            "role": "user",
            "content": "You are given the testCase. However, it is structure with special characters to make inditations and may has some filler sections that are unnecessary."
            "Change the titles of the sections to the corresponding titleType and remove the ... from the title. Titles should not repeat themselves in lower headers. Exec should always be changed to Execution",
        },
    ]
    if coalition.coalitionPrompt:
        messages.append({"role": "system", "content": coalition.coalitionPrompt})

    max_number_of_turns = os.getenv("MAX_NUMBER_OF_TURNS") or 10
    if useAnthropic:
        ai_agent = ClaudeAgent(
            messages=messages, max_number_of_turns=max_number_of_turns, model=agentModel
        )
    else:
        ai_agent = OllamaAgent(
            messages=messages, max_number_of_turns=max_number_of_turns
        )
    await ai_agent.run(testCaseJson=testCaseString, solutionStr=solutionString)
    if ai_agent.latest_test_case_json:
        test_case_path = resultpath.joinpath(filename)
        with open(test_case_path, "w", encoding="utf-8") as file:
            file.write(ai_agent.latest_test_case_json)
    if ai_agent.results:
        results_metrics_path = resultpath.joinpath("results.json")
        createOrExtendResult(
            results=ai_agent.results,
            coalition=coalition,
            resultpath=results_metrics_path,
            executionTime=ai_agent.executionTime,
            numberOfRounds=ai_agent.numberOfLoops,
            loopStopReason=ai_agent.loopStopReason,
        )
