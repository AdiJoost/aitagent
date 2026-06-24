import logging
import os
from typing import List

from anthropic import AsyncAnthropic
from anthropic.types import Message, TextBlock, ToolUseBlock
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from src.llm.agents.base_agent import BaseAgent
from src.model.websocket.websocket_message_type import WebSocketMessageType
from src.model.websocket.websocket_send_dto import WebSocketSendDTO
from src.utilities.agent_testing.test_utilities import getReducedTestcaseFromCall

logger = logging.getLogger(__name__)


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
            streamable_http_client(f"{self.mcp_http}/mcp") as (read, write, _),
            ClientSession(read, write) as session,
        ):
            logger.info("Setup Agent")
            await self._setup(
                session=session, testCaseJson=testCaseJson, solutionStr=solutionStr
            )
            logger.debug("Setup complete")
            logger.debug("Get tools")
            claude_tools = await self._get_tools(session=session)

            logger.debug("Create client")
            client = AsyncAnthropic(
                api_key=os.environ["AZURE_ANTHROPIC_API_KEY"],
                base_url=os.environ["AZURE_ANTHROPIC_ENDPOINT"].rstrip("/"),
            )

            await self.emit_progress(
                WebSocketSendDTO(
                    type=WebSocketMessageType.THINKING, content="Agent setup complete."
                )
            )

            logger.info("Starting Agent Loop")
            await self._run_agent_loop(
                claude_tools=claude_tools, client=client, session=session
            )
            logger.info("Debriefing Agent")
            await self._debrief(session=session)

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
            await self._find_and_send_progress(response)

            tool_use_blocks = [
                block for block in response.content if block.type == "tool_use"
            ]

            if tool_use_blocks:
                logger.debug("Calling tools")
                await self._execute_tools(
                    tool_use_blocks=tool_use_blocks, session=session
                )
            elif self._has_finish_keyword(response):
                logger.info("Finish keyword detected.")
                self.return_message = response.content[0].text
                break
            else:
                self.messages.append({"role": "user", "content": "continue"})
                continue

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
            logger.debug("Response content: type=%s, content=%s", content.type, content)

    async def _find_and_send_progress(self, response: any) -> None:
        for content in response.content:
            if content and content.type == "text":
                await self.emit_progress(
                    WebSocketSendDTO(
                        type=WebSocketMessageType.THINKING, content=content.text
                    )
                )

    async def _send_user_message(self, tool_use_block: ToolUseBlock) -> str:
        msg = (tool_use_block.input.get("message") or "").strip()
        if msg:
            await self.emit_progress(
                WebSocketSendDTO(
                    type=WebSocketMessageType.USER_MESSAGE,
                    content=msg,
                )
            )
            return "message sent to user."
        return "Error: message must not be empty"

    async def _execute_tools(
        self, tool_use_blocks: List[ToolUseBlock], session: ClientSession
    ) -> None:
        tool_results = []
        for block in tool_use_blocks:
            logger.info(f"Calling tool: {block.name}({block.input})")
            self.tools_called.append(f"Calling tool: {block.name}({block.input})")
            if block.name == "send_user_message":
                result = await self._send_user_message(block)
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

    def _has_finish_keyword(self, response: any) -> bool:
        len(response.content) > 0 and response.content[
            0
        ].type == "text" and "TASK_COMPLETE" in response.content[0].text
