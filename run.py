import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from config.loggingSetup import setup_logging
from config.rootPath import getRootPath
from src.llm.agents.manual_agent import ClaudeAgent
from src.singel_worker import update_testcase_single_agent

evaluating_testcase_name = "test-case-id-87-rev-8-dbid-2113.automate.json"


async def main():
    load_dotenv()
    setup_logging()

    mainPath = getRootPath()
    dataPath = mainPath.joinpath("data", "testcases_to_update")
    for filename in os.listdir(dataPath):
        if filename == evaluating_testcase_name:
            filepath = dataPath.joinpath(filename)
            solutionPath = mainPath.joinpath("data", "solutions", filename)
            resultPath = mainPath.joinpath("data", "results", filename[:-5])
            if os.path.isfile(filepath) and os.path.isfile(solutionPath):
                await _run_manual_agent(
                    filepath, solutionPath, resultpath=resultPath, filename=filename
                )
                return


async def _run_manual_agent(
    filepath: Path, solutionpath: Path, resultpath: Path, filename: str
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
            + "1. First call 'get_current_testcase' to see the current state.\n"
            + "2. Then use the appropriate MCP tools to make changes.\n"
            + "Never write code. Always use the provided tool calls. Do not use tools that start with _. Do not provide an explenation, just prompt the tools to execute."
            "When the task is complete, answere with TASK_COMPLETE. Only use ANSWERE_COMPLETE, when you are complete, do not add id in any other instance.",
        },
        {
            "role": "user",
            "content": "You are given the testCase. However, it is structure with .... to make inditations and has some filler sections that are unnecessary. Change the titles of the sections to the corresponding titleType and remove the ... from the title. Remove sections, that are just filler. Remove fragemnts for structuring like multiple !",
        },
    ]

    claude_agent = ClaudeAgent(messages=messages, max_number_of_turns=25)
    await claude_agent.run(testCaseJson=testCaseString, solutionStr=solutionString)
    if claude_agent.latest_test_case_json:
        test_case_path = resultpath.joinpath(filename)
        with open(test_case_path, "w", encoding="utf-8") as file:
            file.write(claude_agent.latest_test_case_json)
    if claude_agent.results:
        results_metrics_path = resultpath.joinpath("results.json")
        with open(results_metrics_path, "w", encoding="utf-8") as file:
            file.write(json.dumps(claude_agent.results))


if __name__ == "__main__":
    asyncio.run(main())
