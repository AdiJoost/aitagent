import asyncio
import json
import logging
import os
from typing import List, Optional

from anthropic import AsyncAnthropic
from pydantic import ValidationError

logger = logging.getLogger(__name__)

from anthropic.types import Message
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult

from src.model.evaluation_dto.update_dto_list import UpdateDTOList
from src.utilities.telemetry.telemetry import Telemetry
from src.utilities.telemetry.trace_provider import TraceProvider


class ClaudeAgent:
    def __init__(
        self,
        messages: list,
        model: str = "claude-opus-4-6",
        max_tokens: int = 500,
        temperature: float = 0,
        max_number_of_turns: int = 10,
        mcp_http: str = "http://127.0.0.1:8000/mcp",
        with_trace_provicer: bool = False,
        chatty: bool = False,
    ):
        # Anthropic requires system prompt as a separate parameter, not in messages
        self.system_prompt = None
        self.messages = []
        for msg in messages:
            if msg["role"] == "system":
                self.system_prompt = msg["content"]
            else:
                self.messages.append(msg)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_number_of_turns = max_number_of_turns
        self.mcp_http = mcp_http
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
        claude_tools = []
        for t in tools.tools:
            if not t.name.startswith("_"):
                claude_tools.append(
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.inputSchema,
                    }
                )
        return claude_tools

    async def run(self, testCaseJson: str, solutionStr: str):
        async with (
            streamable_http_client(self.mcp_http) as (read, write, _),
            ClientSession(read, write) as session,
        ):
            await self._setup(
                session=session, testCaseJson=testCaseJson, solutionStr=solutionStr
            )
            claude_tools = await self._get_tools(session=session)

            client = AsyncAnthropic(
                api_key=os.environ["AZURE_ANTHROPIC_API_KEY"],
                base_url=os.environ["AZURE_ANTHROPIC_ENDPOINT"].rstrip("/"),
            )

            logger.debug("Starting Agent Loop")
            await self._run_agent_loop(
                claude_tools=claude_tools, client=client, session=session
            )

            await self._debrief(session=session)

    async def _debrief(self, session: ClientSession) -> None:

        accuracy_afterwards = await session.call_tool("_get_result_metrics")
        if self._response_has_text(accuracy_afterwards):
            self.results = json.loads(
                accuracy_afterwards.content[0].text
            )

        latest = await session.call_tool("get_current_testcase")
        if self._response_has_text(latest):
            self.latest_test_case_json = latest.content[0].text

        await self._get_update_dto_list(session=session)

    async def _get_model_response(
        self, client: AsyncAnthropic, claude_tools: List
    ) -> Message:
        logger.debug("calling Model")
        create_kwargs = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            tools=claude_tools,
            messages=self.messages,
        )
        if self.system_prompt:
            create_kwargs["system"] = self.system_prompt
        return await client.messages.create(**create_kwargs)

    async def _run_agent_loop(
        self, client: AsyncAnthropic, claude_tools: List, session: ClientSession
    ) -> None:
        number_of_calls = 0
        while number_of_calls < self.max_number_of_turns:
            number_of_calls += 1

            response = await self._get_model_response(
                client=client, claude_tools=claude_tools
            )

            self.messages.append({"role": "assistant", "content": response.content})

            # Check if there are any tool_use blocks (regardless of stop_reason)
            tool_use_blocks = [
                block for block in response.content if block.type == "tool_use"
            ]

            if tool_use_blocks:
                tool_results = []
                for block in tool_use_blocks:
                    logger.info(f"Calling tool: {block.name}({block.input})")
                    self.tools_called.append(
                        f"Calling tool: {block.name}({block.input})"
                    )
                    result = await session.call_tool(block.name, arguments=block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        }
                    )
                self.messages.append({"role": "user", "content": tool_results})
            elif (
                len(response.content) > 0
                and response.content[0].type == "text"
                and "TASK_COMPLETE" in response.content[0].text
            ):
                logger.info("Breaking early")
                break
            else:
                # No tool calls — the model considers the task complete
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
