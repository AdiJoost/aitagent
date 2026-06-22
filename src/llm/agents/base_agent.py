import asyncio
import logging
import os
from typing import Any, Callable, Coroutine, List, Optional

from mcp import ClientSession
from mcp.types import CallToolResult
from pydantic_core import ValidationError

from src.model.evaluation_dto.update_dto_list import UpdateDTOList
from src.model.result.test_stats import TestStats
from src.model.websocket.websocket_send_dto import WebSocketSendDTO

logger = logging.getLogger(__name__)

# Type alias for progress callbacks: async functions that receive an event dict
ProgressCallback = Callable[[dict], Coroutine[Any, Any, None]]


class BaseAgent:
    def __init__(
        self,
        model: str = None,
        max_tokens: int = 2500,
        temperature: float = 0,
        max_number_of_turns: int = 10,
        on_progress: Optional[ProgressCallback] = None,
    ):
        self.messages = []
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_number_of_turns = max_number_of_turns

        self.model = model or os.getenv("AGENT_MODEL")
        logger.debug(f"Model is: {self.model}")

        self.mcp_http = os.getenv("MCP_HOST")
        logger.debug(f"MCP_HTTP is: {self.mcp_http}")

        self.ollama_host = os.getenv("OLLAMA_HOST")
        logger.debug(f"OLLAMA_HOST is: {self.ollama_host}")

        self.with_trace_provider = False
        self.results: TestStats = None
        self.tools_called = []
        self.latest_test_case_json: Optional[str] = None
        self.updateDtoList: Optional[List[UpdateDTOList]] = None
        self._on_progress = on_progress
        self.return_message = None

    async def emit_progress(self, event: WebSocketSendDTO) -> None:
        if self._on_progress:
            await self._on_progress(event.model_dump())

    async def _get_tools(self, session: ClientSession):
        raise NotImplementedError("Subclasses must implement this method.")

    async def run(self, testCaseJson: str, solutionStr: str):
        raise NotImplementedError("Subclasses must implement this method.")

    async def _setup(self, session: ClientSession, testCaseJson: str, solutionStr: str):
        await session.initialize()

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

    async def _debrief(self, session: ClientSession) -> None:

        accuracy_afterwards = await session.call_tool("_get_result_metrics")
        if self._response_has_text(accuracy_afterwards):
            try:
                self.results = TestStats.model_validate_json(
                    accuracy_afterwards.content[0].text
                )
            except ValidationError as e:
                logger.error(f"Error in geting results, {e}")

        latest = await session.call_tool("get_current_testcase")
        if self._response_has_text(latest):
            self.latest_test_case_json = latest.content[0].text

        await self._get_update_dto_list(session=session)

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
