import asyncio
import json
import logging
import os
import time
from typing import List, Optional

from anthropic import AsyncAnthropic
from pydantic import ValidationError

from src.llm.agents.base_agent import BaseAgent
from src.model.result.test_stats import TestStats
from src.model.websocket.websocket_message_type import WebSocketMessageType
from src.model.websocket.websocket_send_dto import WebSocketSendDTO
from src.utilities.agent_testing.test_utilities import \
    getReducedTestcaseFromCall

logger = logging.getLogger(__name__)

from anthropic.types import Message, TextBlock, ToolUseBlock
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult

from src.model.evaluation_dto.update_dto_list import UpdateDTOList
from src.utilities.telemetry.telemetry import Telemetry
from src.utilities.telemetry.trace_provider import TraceProvider


class ClaudeAgent(BaseAgent):
    def __init__(
        self,
        messages: list,
        model: str = "claude-opus-4-6",
        max_tokens: int = 500,
        temperature: float = 0,
        max_number_of_turns: int = 10,
        on_progress=None,
    ):
        super().__init__(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            max_number_of_turns=max_number_of_turns,
            on_progress=on_progress,
        )
        # Anthropic requires system prompt as a separate parameter, not in messages
        self.system_prompt = None
        self.messages = []
        for msg in messages:
            if msg["role"] == "system":
                self.system_prompt = msg["content"]
            else:
                self.messages.append(msg)

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
            logger.info("Setup Agent")
            await self._setup(
                session=session, testCaseJson=testCaseJson, solutionStr=solutionStr
            )
            logger.info("Setup complete")
            logger.info("Get tools")
            claude_tools = await self._get_tools(session=session)

            logger.info("Create client")
            client = AsyncAnthropic(
                api_key=os.environ["AZURE_ANTHROPIC_API_KEY"],
                base_url=os.environ["AZURE_ANTHROPIC_ENDPOINT"].rstrip("/"),
            )

            await self.emit_progress(
                WebSocketSendDTO(
                    type=WebSocketMessageType.THINKING, content="Agent setup complete."
                )
            )

            logger.debug("Starting Agent Loop")
            await self._run_agent_loop(
                claude_tools=claude_tools, client=client, session=session
            )
            logger.debug("Debriefing Agent")
            await self._debrief(session=session)

    async def _get_model_response(
        self, client: AsyncAnthropic, claude_tools: List
    ) -> Message:
        logger.debug("---calling Model with---")
        if len(self.messages) > 0:
            logger.debug(f"{self.messages[-1]}")
        create_kwargs = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            tools=claude_tools,
            messages=self.messages,
        )
        if self.system_prompt:
            create_kwargs["system"] = self.system_prompt
        response = await client.messages.create(**create_kwargs)

        self._log_model_response(response)

        return response

    def _log_model_response(self, response: Message) -> None:
        if not response:
            logger.warning("Got a null response.")
            return
        if response.role:
            logger.debug("Role: %s", response.role)
        for content in response.content:
            if isinstance(content, TextBlock):
                logger.debug("Text: %s", content.text)

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

            for content in response.content:
                logger.debug("Response content: type=%s, content=%s", content.type, content)

            for content in response.content:
                if content and content.type == "text":
                    await self.emit_progress(
                        WebSocketSendDTO(
                            type=WebSocketMessageType.THINKING, content=content.text
                        )
                    )

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
                    if block.name == "send_user_message":
                        msg = (block.input.get("message") or "").strip()
                        if msg:
                            await self.emit_progress(WebSocketSendDTO(
                                type=WebSocketMessageType.USER_MESSAGE,
                                content=response.content[0].text,
                            ))
                            result = "message sent to user."
                        else:
                            try:
                                await self.emit_progress(WebSocketSendDTO(
                                type=WebSocketMessageType.USER_MESSAGE,
                                content=block.input.get("message", ""),
                                ))
                                result = "message sent to user."
                            except:
                                result = "Error: message must not be empty"
                    else:
                        result = await session.call_tool(block.name, arguments=block.input)
                    if block.name == "get_current_testcase":
                        result = getReducedTestcaseFromCall(result)
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
                self.return_message = response.content[0].text
                break
            else:
                self.messages.append({"role": "user", "content": "continue"})
                continue

    def _get_message_tool(self) -> any:
        return {
           "name": "send_user_message",
            "description": "Send a message to the user when you have an interesting finding, insight, or need to communicate something noteworthy. Use sparingly — only for information the user would genuinely want to see. Include the message formatted in md and use the md in the function call.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The message to display to the user."}
                },
                "required": ["message"], 
            }
        }