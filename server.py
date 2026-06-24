import asyncio
import json
import logging
import traceback
import uuid
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, model_validator
from sse_starlette.sse import EventSourceResponse

from config.loggingSetup import setup_logging
from src.application.the_main_running_loop import the_main_running_loop
from src.llm.agents.claude_agent import ClaudeAgent
from src.model.websocket.websocket_message_type import WebSocketMessageType
from src.model.websocket.websocket_send_dto import WebSocketSendDTO

# load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

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
    maxTurns: int = 5

    @model_validator(mode="after")
    def stringify_json_fields(self):
        if not isinstance(self.testCaseString, str):
            self.testCaseString = json.dumps(self.testCaseString)
        if not isinstance(self.solutionString, str):
            self.solutionString = json.dumps(self.solutionString)
        return self


@app.post("/loop/run")
async def run_loop():
    await the_main_running_loop()


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

    agent = ClaudeAgent(messages=messages, max_number_of_turns=request.maxTurns)

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


@app.websocket("/ws/run")
async def ws_run(websocket: WebSocket):
    await websocket.accept()

    try:
        start_msg = await websocket.receive_json()
        if start_msg.get("type") != "start":
            webSocketSendDTO = WebSocketSendDTO(
                type=WebSocketMessageType.ERROR, content="Expected type: start"
            )
            await websocket.send_json(webSocketSendDTO.model_dump_json())
            await websocket.close()
            return

        test_case = start_msg.get("testCaseString")
        solution = start_msg.get("solutionString")
        user_prompt = start_msg.get("userPrompt", "")
        max_turns = start_msg.get("maxTurns", 5)

        if not isinstance(test_case, str):
            test_case = json.dumps(test_case)
        if not isinstance(solution, str):
            solution = json.dumps(solution)

        async def on_progress(event: dict):
            await websocket.send_json(event)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert test designer. You modify testcases using MCP tool calls and give feedback to the user.\n"
                    "IMPORTANT: You MUST use tool calls to interact with the testcase.\n"
                    "1. First call 'get_current_testcase' to see the current state.\n"
                    "2. Then use the appropriate MCP tools to make changes or give feedback to the user.\n"
                    "Never write code. Always use the provided tool calls. "
                    "When the task is complete, answere with TASK_COMPLETE. "
                    "Only use ANSWERE_COMPLETE, when you are complete, do not add id in any other instance."
                ),
            },
            {"role": "user", "content": user_prompt},
        ]

        agent = ClaudeAgent(
            messages=messages,
            max_number_of_turns=max_turns,
            on_progress=on_progress,
        )

        # Run the agent as a task so we can cancel it
        agent_task = asyncio.create_task(
            agent.run(testCaseJson=test_case, solutionStr=solution)
        )

        # Listen for incoming messages (cancel command) while agent runs
        listen_task = asyncio.create_task(_listen_for_cancel(websocket, agent_task))

        try:
            await agent_task
            result = {
                "type": WebSocketMessageType.DONE,
                "message": agent.return_message
                if agent.return_message
                else "Task Completed",
                "toolsCalled": agent.tools_called,
                "updateDTO": agent.updateDtoList.model_dump()
                if agent.updateDtoList
                else None,
            }
            await websocket.send_json(result)
        except asyncio.CancelledError:
            await websocket.send_json({"event": "cancelled"})
        finally:
            listen_task.cancel()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        traceback.print_exc()
        try:
            await websocket.send_json(
                WebSocketSendDTO(type=WebSocketMessageType.ERROR, content=str(e))
            )
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


async def _listen_for_cancel(websocket: WebSocket, agent_task: asyncio.Task):
    """Listens for a cancel message from the client and cancels the agent task."""
    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("type") == "cancel":
                agent_task.cancel()
                return
    except (WebSocketDisconnect, asyncio.CancelledError):
        # Connection closed or listener was cancelled because agent finished
        pass
