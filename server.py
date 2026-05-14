import asyncio
import json
import logging
import traceback
import uuid
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, model_validator
from sse_starlette.sse import EventSourceResponse

from config.loggingSetup import setup_logging
from src.llm.agents.manual_agent import ClaudeAgent

load_dotenv()
setup_logging()

import os

MCP_URL = os.getenv("MCP_URL", "http://host.docker.internal:8000/mcp")

app = FastAPI(title="AI Test Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    testCaseString: Any
    solutionString: Any
    userPrompt: str
    maxTurns: int = 50

    @model_validator(mode="after")
    def stringify_json_fields(self):
        if not isinstance(self.testCaseString, str):
            self.testCaseString = json.dumps(self.testCaseString)
        if not isinstance(self.solutionString, str):
            self.solutionString = json.dumps(self.solutionString)
        return self


@app.post("/api/run")
async def run_agent(request: RunRequest):
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert test designer. You modify testcases using MCP tool calls.\n"
                "IMPORTANT: You MUST use tool calls to interact with the testcase.\n"
                "1. First call 'get_current_testcase' to see the current state.\n"
                "2. Then use the appropriate MCP tools to make changes.\n"
                "Never write code. Always use the provided tool calls. Do not use tools that start with _. "
                "Do not provide an explenation, just prompt the tools to execute."
                "When the task is complete, answere with TASK_COMPLETE. "
                "Only use ANSWERE_COMPLETE, when you are complete, do not add id in any other instance."
            ),
        },
        {
            "role": "user",
            "content": request.userPrompt,
        },
    ]

    agent = ClaudeAgent(
        messages=messages, max_number_of_turns=request.maxTurns, mcp_http=MCP_URL
    )

    try:
        await agent.run(
            testCaseJson=request.testCaseString,
            solutionStr=request.solutionString,
        )
        result = {
            "results": agent.results,
            # "testCase": agent.latest_test_case_json if isinstance(agent.latest_test_case_json, str) else str(agent.latest_test_case_json),
            "toolsCalled": agent.tools_called,
            "updateDTO": agent.updateDtoList,
        }
        print(
            f"Returning result, testCase type: {type(agent.latest_test_case_json)}, results types: {[(k, type(v)) for k, v in agent.results.items()]}"
        )
        return result
    except BaseException as e:
        # Unwrap ExceptionGroup / TaskGroup errors to see root cause
        if isinstance(e, BaseExceptionGroup):  # noqa: F821
            for exc in e.exceptions:
                traceback.print_exception(type(exc), exc, exc.__traceback__)
        else:
            traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok"}
