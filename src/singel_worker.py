from autogen import AssistantAgent, ConversableAgent

from src.llm.gates.azure_anthropic_gate import AzureAnthropicGateFactory
from src.llm.gates.ollama_gate import OllamaGateFactory
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession
from autogen.mcp import create_toolkit

from src.utilities.telemetry.telemetry import Telemetry
from src.utilities.telemetry.trace_provider import TraceProvider

async def update_testcase_single_agent(user_prompt: str, testCaseJSON: str, solutionStr: str):
    ollama_config = OllamaGateFactory(
            model_name="gemma4:31b"
        ).build()
    azure_config = AzureAnthropicGateFactory(model_name="claude-opus-4-6").build()
    async with (streamable_http_client("http://127.0.0.1:8000/mcp") as (read, write, _), ClientSession(read, write) as session,):
        await session.initialize()
        tracer_provider = TraceProvider.set_trace_provider()
        Telemetry.setup(tracer_provider=tracer_provider, capture_messages=True)
        toolkit = await create_toolkit(session=session,
                                        use_mcp_tools=True,
                                        use_mcp_resources=False)

        # Call a tool before the agent runs
        await session.call_tool("_load_testcase", arguments={"testcaseAsString": testCaseJSON})
        await session.call_tool("_load_solution", arguments={"solutionAsString": solutionStr})
        accuracy_in_advanced = await session.call_tool("_get_result_metrics")
        loaded_testcase = await session.call_tool("get_current_testcase")

        agent = AssistantAgent(
            name="agent",
            system_message=(
                "You are an expert test designer. You modify testcases using MCP tool calls.\n"
                "IMPORTANT: You MUST use tool calls to interact with the testcase.\n"
                "1. First call 'get_current_testcase' to see the current state.\n"
                "2. Then use the appropriate MCP tools to make changes.\n"
                "Never write code. Always use the provided tool calls. Do not use tools that start with _. Do not provide an explenation, just prompt the tools to execute."
            ),
            llm_config=azure_config,
        )

        user_proxy = ConversableAgent(
            name="user_proxy",
            llm_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=4
        )

        toolkit.register_for_llm(agent)
        toolkit.register_for_execution(user_proxy)

        message = user_prompt + f"\nThis is the currently loaded test case: {loaded_testcase}"

        result = await user_proxy.a_initiate_chat(agent, message=message, max_turns=10)
        accuracy_after = await session.call_tool("_get_result_metrics")
        print(result)

        print(f"\n\n------ Metrics ------\nAccuracy before: {accuracy_in_advanced}\nAccuracy afterwards: {accuracy_after}")



async def _update_testcase_single_agent(user_prompt: str, testCaseJSON: str, solutionStr: str):
    ollama_config = OllamaGateFactory(
            model_name="gemma4:31b"
        ).build()
    azure_config = AzureAnthropicGateFactory(model_name="claude-opus-4-6").build()
    async with (streamable_http_client("http://127.0.0.1:8000/mcp") as (read, write, _), ClientSession(read, write) as session,):
        await session.initialize()
        tracer_provider = TraceProvider.set_trace_provider()
        Telemetry.setup(tracer_provider=tracer_provider, capture_messages=True)
        toolkit = await create_toolkit(session=session,
                                        use_mcp_tools=True,
                                        use_mcp_resources=False)

        # Call a tool before the agent runs
        await session.call_tool("_load_testcase", arguments={"testcaseAsString": testCaseJSON})
        await session.call_tool("_load_solution", arguments={"solutionAsString": solutionStr})
        accuracy_in_advanced = await session.call_tool("_get_result_metrics")
        loaded_testcase = await session.call_tool("get_current_testcase")

        agent = AssistantAgent(
            name="agent",
            system_message=(
                "You are an expert test designer. You modify testcases using MCP tool calls.\n"
                "IMPORTANT: You MUST use tool calls to interact with the testcase.\n"
                "1. First call 'get_current_testcase' to see the current state.\n"
                "2. Then use the appropriate MCP tools to make changes.\n"
                "Never write code. Always use the provided tool calls. Do not use tools that start with _. Do not provide an explenation, just prompt the tools to execute."
            ),
            llm_config=azure_config,
            max_consecutive_auto_reply=4,
            human_input_mode="NEVER"
        )

        message = user_prompt + f"\nThis is the currently loaded test case: {loaded_testcase}"

        cut_tools= [tool for tool in toolkit.tools if not tool.name.startswith("_")]
        result = await agent.a_run(message=message, max_turns=4, tools=cut_tools, user_input=False)
        accuracy_after = await session.call_tool("_get_result_metrics")
        print(result)

        print(f"\n\n------ Metrics ------\nAccuracy before: {accuracy_in_advanced}\nAccuracy afterwards: {accuracy_after}")