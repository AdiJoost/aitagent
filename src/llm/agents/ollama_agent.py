import asyncio
import json
import logging
import os
from typing import List, Optional

from ollama import AsyncClient
from pydantic import ValidationError

logger = logging.getLogger(__name__)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult

from src.model.evaluation_dto.update_dto_list import UpdateDTOList
from src.utilities.telemetry.telemetry import Telemetry
from src.utilities.telemetry.trace_provider import TraceProvider


class OllamaAgent:
    def __init__(
        self,
        messages: list,
        model: str = "qwen2.5:14b",
        max_tokens: int = 500,
        temperature: float = 0,
        max_number_of_turns: int = 10,
        mcp_http: str = "http://127.0.0.1:8000/mcp",
        ollama_host: str = "http://127.0.0.1:11434",
        with_trace_provicer: bool = False,
        chatty: bool = False,
    ):
        self.messages = list(messages)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_number_of_turns = max_number_of_turns
        self.mcp_http = mcp_http
        self.ollama_host = ollama_host
        self.with_trace_provider = with_trace_provicer
        self.results = {}
        self.tools_called = []
        self.latest_test_case_json: Optional[str] = None
        self.updateDtoList: Optional[List[UpdateDTOList]] = None
        self.chatty = chatty

    async def _setup(self, session: ClientSession, testCaseJson: str, solutionStr: str):
        await session.initialize()
        if self.with_trace_provider:
            logger.info("Setting trace provider")
            tracer_provider = TraceProvider.set_trace_provider()
            Telemetry.setup(tracer_provider=tracer_provider, capture_messages=True)

        logger.info("Setting Testcase")
        await session.call_tool(
            "_load_testcase", arguments={"testcaseAsString": testCaseJson}
        )

        logger.info("Setting solution")
        await session.call_tool(
            "_load_solution", arguments={"solutionAsString": solutionStr}
        )
        logger.info("getting current test case json")
        self.latest_test_case_json = await session.call_tool("get_current_testcase")

    def _response_has_text(self, response: Optional[CallToolResult]) -> bool:
        if not response or not response.content or len(response.content) < 1:
            logger.warning("Response entity has no text.")
            return False
        return True

    async def _get_tools(self, session: ClientSession):
        tools = await session.list_tools()
        ollama_tools = []
        for t in tools.tools:
            if not t.name.startswith("_"):
                ollama_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema,
                        },
                    }
                )
        return ollama_tools

    async def run(self, testCaseJson: str, solutionStr: str):
        async with (
            streamable_http_client(self.mcp_http) as (read, write, _),
            ClientSession(read, write) as session,
        ):
            await self._setup(
                session=session, testCaseJson=testCaseJson, solutionStr=solutionStr
            )
            ollama_tools = await self._get_tools(session=session)

            client = AsyncClient(host=self.ollama_host)

            logger.debug("Starting Agent Loop")
            await self._run_agent_loop(
                ollama_tools=ollama_tools, client=client, session=session
            )

            await self._debrief(session=session)

    async def _debrief(self, session: ClientSession) -> None:

        accuracy_afterwards = await session.call_tool("_get_result_metrics")
        if self._response_has_text(accuracy_afterwards):
            try:
                self.results = json.loads(accuracy_afterwards.content[0].text)
            except json.JSONDecodeError as e:
                logger.error(f"Error in geting results, {e}")

        latest = await session.call_tool("get_current_testcase")
        if self._response_has_text(latest):
            self.latest_test_case_json = latest.content[0].text

        await self._get_update_dto_list(session=session)

    async def _get_model_response(
        self, client: AsyncClient, ollama_tools: List
    ) -> dict:
        logger.debug("calling Model")
        response = await client.chat(
            model=self.model,
            messages=self.messages,
            tools=ollama_tools,
            options={
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
            },
        )
        return response

    async def _run_agent_loop(
        self, client: AsyncClient, ollama_tools: List, session: ClientSession
    ) -> None:
        number_of_calls = 0
        while number_of_calls < self.max_number_of_turns:
            number_of_calls += 1

            response = await self._get_model_response(
                client=client, ollama_tools=ollama_tools
            )

            assistant_message = {
                "role": "assistant",
                "content": response.message.content,
            }
            if response.message.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in response.message.tool_calls
                ]
            self.messages.append(assistant_message)

            if response.message.tool_calls:
                for tc in response.message.tool_calls:
                    tool_name = tc.function.name
                    tool_args = tc.function.arguments
                    logger.info(f"Calling tool: {tool_name}({tool_args})")
                    self.tools_called.append(f"Calling tool: {tool_name}({tool_args})")
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    self.messages.append(
                        {
                            "role": "tool",
                            "content": str(result),
                        }
                    )
            elif (
                response.message.content and "TASK_COMPLETE" in response.message.content
            ):
                logger.info("Breaking early")
                break
            else:
                self.messages.append({"role": "user", "content": "continue"})
                continue

    async def _get_update_dto_list(self, session: ClientSession) -> None:
        response = await session.call_tool("_get_changes")

        if self._response_has_text(response):
            updateDTOListAsString = response.content[0].text
            logger.info("UpdateDTOList retrieved: ")
            logger.info(updateDTOListAsString)
            try:
                self.updateDtoList = UpdateDTOList.model_validate_json(
                    updateDTOListAsString
                )
            except ValidationError:
                logger.error(f"Failed to parse UpdateDTOList: {updateDTOListAsString}")
                self.updateDtoList = None
