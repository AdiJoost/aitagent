import asyncio
import json
import logging
import os
from typing import List, Optional

from ollama import AsyncClient, Client
from opentelemetry import trace
from pydantic import ValidationError

from src.llm.agents.base_agent import BaseAgent
from src.model.result.test_stats import TestStats
from src.utilities.agent_testing.test_utilities import \
    getReducedTestcaseFromCall

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult

from src.model.evaluation_dto.update_dto_list import UpdateDTOList
from src.utilities.telemetry.telemetry import Telemetry
from src.utilities.telemetry.trace_provider import TraceProvider


class OllamaAgent(BaseAgent):
    def __init__(
        self,
        messages: list,
        model: str = "gemma4:latest",
        max_tokens: int = 2500,
        temperature: float = 0,
        max_number_of_turns: int = 10,
    ):
        super().__init__(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            max_number_of_turns=max_number_of_turns,
        )
        self.messages = list(messages)
        self._pull_model()

    def _pull_model(self) -> None:
        client = Client(host=self.ollama_host)
        local_models = client.list().models
        if any(m.model == self.model for m in local_models):
            logger.info(f"Model '{self.model}' already available locally.")
            return
        logger.info(f"Model '{self.model}' not found locally. Pulling...")
        client.pull(self.model)
        logger.info(f"Model '{self.model}' pulled successfully.")

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
            logger.info("Setup Agent")
            await self._setup(
                session=session, testCaseJson=testCaseJson, solutionStr=solutionStr
            )
            logger.info("Setup complete")
            logger.info("Get tools")
            ollama_tools = await self._get_tools(session=session)

            logger.info("Create client")
            client = AsyncClient(host=self.ollama_host)

            logger.debug("Starting Agent Loop")
            await self._run_agent_loop(
                ollama_tools=ollama_tools, client=client, session=session
            )

            logger.debug("Debriefing Agent")
            await self._debrief(session=session)

    async def _get_model_response(
        self, client: AsyncClient, ollama_tools: List
    ) -> dict:
        logger.debug("---calling Model with---")
        if len(self.messages) > 0:
            logger.debug(f"{self.messages[-1]}")
        
        response = await client.chat(
            model=self.model,
            messages=self.messages,
            tools=ollama_tools,
            options={
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
            },
        )
        logger.debug("Role: %s", response.message.role)
        logger.debug("Content: %s", response.message.content)

        if getattr(response.message, "tool_calls", None):
            logger.debug("Tool calls: %s", response.message.tool_calls)

        logger.debug("Full response: %s", response)
        return response

    async def _run_agent_loop(
        self, client: AsyncClient, ollama_tools: List, session: ClientSession
    ) -> None:
            number_of_calls = 0
            while number_of_calls < self.max_number_of_turns:
                number_of_calls += 1

                logger.info("Get Model Response")
                response = await self._get_model_response(
                    client=client, ollama_tools=ollama_tools
                )

                assistant_message = {
                    "role": "assistant",
                    "content": response.message.content,
                }
                if response.message.tool_calls:
                    logger.info("Toolcall detected")
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
                        if tool_name == "get_current_testcase":
                            tool_args = tc.function.arguments
                            logger.info(f"Calling tool: {tool_name}({tool_args})")
                            self.tools_called.append(f"Calling tool: {tool_name}({tool_args})")
                            result = await session.call_tool(tool_name, arguments=tool_args)
                            self.messages.append(
                                {
                                    "role": "tool",
                                    "content": getReducedTestcaseFromCall(message=result),
                                }
                            )
                        else:
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

    
