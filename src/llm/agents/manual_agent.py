import json
import os
import asyncio
from anthropic import AsyncAnthropic

from mcp import ClientSession, StdioServerParameters
from mcp.client.streamable_http import streamable_http_client
from mcp.client.stdio import stdio_client

from src.utilities.telemetry.telemetry import Telemetry
from src.utilities.telemetry.trace_provider import TraceProvider

class ClaudeAgent():

    def __init__(self, messages: list, model: str="claude-opus-4-6", max_tokens:int=500, temperature:float=0, max_number_of_turns:int=10, mcp_http:str="http://127.0.0.1:8000/mcp", with_trace_provicer:bool=False):
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
        self.with_trace_provider=with_trace_provicer
        self.results={}
        self.tools_called=[]
        self.latest_test_case_json:str=None
    
    async def _setup(self, session: ClientSession, testCaseJson: str, solutionStr: str):
            await session.initialize()
            if(self.with_trace_provider):
                tracer_provider = TraceProvider.set_trace_provider()
                Telemetry.setup(tracer_provider=tracer_provider, capture_messages=True)

            await session.call_tool("_load_testcase", arguments={"testcaseAsString": testCaseJson})
            await session.call_tool("_load_solution", arguments={"solutionAsString": solutionStr})
            accuracy_in_advance = await session.call_tool("_get_result_metrics")
            self.results["accuracy_in_advance"] = json.loads(accuracy_in_advance.content[0].text)
            self.latest_test_case_json = await session.call_tool("get_current_testcase")
            

    async def _get_tools(self, session:ClientSession):
            tools = await session.list_tools()
            claude_tools = []
            for t in tools.tools:
                if not t.name.startswith("_"):
                    claude_tools.append({
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.inputSchema,
                    })
            return claude_tools

    async def run(self, testCaseJson: str, solutionStr: str):
        async with (streamable_http_client(self.mcp_http) as (read, write, _), ClientSession(read, write) as session,):
            await self._setup(session=session, testCaseJson=testCaseJson, solutionStr=solutionStr)
            claude_tools = await self._get_tools(session=session)
            client = AsyncAnthropic(
                api_key=os.environ["AZURE_ANTHROPIC_API_KEY"],
                base_url=os.environ["AZURE_ANTHROPIC_ENDPOINT"].rstrip("/"),
            )

            number_of_calls = 0
            while number_of_calls < self.max_number_of_turns:
                print("--- calling Model ---")
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
                
                number_of_calls += 1

                print(f"Response: {response.content}")

                self.messages.append({"role": "assistant", "content": response.content})

                # Check if there are any tool_use blocks (regardless of stop_reason)
                tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

                if tool_use_blocks:
                    tool_results = []
                    for block in tool_use_blocks:
                        print(f"Calling tool: {block.name}({block.input})")
                        self.tools_called.append(f"Calling tool: {block.name}({block.input})")
                        result = await session.call_tool(block.name, arguments=block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })
                    self.messages.append({"role": "user", "content": tool_results})
                elif (len(response.content) > 0 and response.content[0].type == "text" and "TASK_COMPLETE" in response.content[0].text):
                    print("Breaking early")
                    break
                else:
                    # No tool calls — the model considers the task complete
                    self.messages.append({"role": "user", "content": "continue"})
                    continue
            print(f"Numbers of rounds: {number_of_calls}")
            accuracy_afterwards = await session.call_tool("_get_result_metrics")
            self.results["accuracy_afterwards"] = json.loads(accuracy_afterwards.content[0].text)
            latest = await session.call_tool("get_current_testcase")
            self.latest_test_case_json = latest.content[0].text