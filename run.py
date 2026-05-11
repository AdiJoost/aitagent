import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from config.rootPath import getRootPath
from src.ait_changer import  generate_ne_names, tryin
from src.better_changer import update_testcase
from src.eros import generate_date
from src.llm.agents.manual_agent import ClaudeAgent
from src.singel_worker import update_testcase_single_agent


async def main():
    load_dotenv()
    await tryin()

async def run_testcase():
    systemprompt = "Write a bachelorsthesis about the import of bananas."
    await update_testcase(systemprompt)

async def run_single_agent():
    load_dotenv()

    mainPath = getRootPath()
    dataPath = mainPath.joinpath("data", "testcases_to_update")
    for filename in os.listdir(dataPath):
        if (filename == "test-case-id-67-rev-0-dbid-79.automate.json"):
            filepath = dataPath.joinpath(filename)
            solutionPath = mainPath.joinpath("data", "solutions", filename)
            if os.path.isfile(filepath) and os.path.isfile(solutionPath):
                await process_file(filepath, solutionPath)
                return
        
async def process_file(filepath, solutionpath):
    testCaseString = None
    solutionString = None
    with open(filepath, "r") as file:
        testCaseString = file.read()
    with open(solutionpath, "r") as file:
        solutionString = file.read()
    userPromt = "You are given the testCase. However, it is structure with .... to make inditations. Change the titles of the sections to the corresponding titleType and remove the ... or any prefix () from the title. Use Header 1 for the outer most sections and use standard for the inner most sections. For the others, use an appropiate header."
    await update_testcase_single_agent(userPromt, testCaseString, solutionString)


async def run_manual_agent():
    load_dotenv()

    mainPath = getRootPath()
    dataPath = mainPath.joinpath("data", "testcases_to_update")
    for filename in os.listdir(dataPath):
        if (filename == "test-case-id-67-rev-0-dbid-79.automate.json"):
            filepath = dataPath.joinpath(filename)
            solutionPath = mainPath.joinpath("data", "solutions", filename)
            resultPath = mainPath.joinpath("data", "results", filename[:-5])
            if os.path.isfile(filepath) and os.path.isfile(solutionPath):
                await _run_manual_agent(filepath, solutionPath, resultpath=resultPath, filename=filename)
                return

async def _run_manual_agent(filepath:Path, solutionpath:Path, resultpath:Path, filename: str):
    os.makedirs(resultpath, exist_ok=True)
    testCaseString = None
    solutionString = None
    with open(filepath, "r") as file:
        testCaseString = file.read()
    with open(solutionpath, "r") as file:
        solutionString = file.read()
    messages = [
         {
              "role":"system",
              "content": "You are an expert test designer. You modify testcases using MCP tool calls.\n" +
                "IMPORTANT: You MUST use tool calls to interact with the testcase.\n" +
                "1. First call 'get_current_testcase' to see the current state.\n" +
                "2. Then use the appropriate MCP tools to make changes.\n" +
                "Never write code. Always use the provided tool calls. Do not use tools that start with _. Do not provide an explenation, just prompt the tools to execute."
                "When the task is complete, answere with TASK_COMPLETE. Only use ANSWERE_COMPLETE, when you are complete, do not add id in any other instance." 
         },
         {
            "role":"user",
            "content": "You are given the testCase. However, it is structure with .... to make inditations and has some filler sections that are unnecessary. Change the titles of the sections to the corresponding titleType and remove the ... from the title. Remove sections, that are just filler. Remove fragemnts for structuring like multiple !"
        }
    ]

    claude_agent = ClaudeAgent(messages=messages, max_number_of_turns=50)
    await claude_agent.run(testCaseJson=testCaseString, solutionStr=solutionString)
    print(claude_agent.results)
    if claude_agent.latest_test_case_json:
        test_case_path = resultpath.joinpath(filename)
        with open(test_case_path, "w", encoding="utf-8") as file:
            file.write(claude_agent.latest_test_case_json)
        results_metrics_path = resultpath.joinpath("results.json")
        with open(results_metrics_path, "w", encoding="utf-8") as file:
            file.write(json.dumps(claude_agent.results))



if __name__ == "__main__":
    asyncio.run(run_manual_agent())
    
 