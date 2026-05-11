from autogen import ConversableAgent, GroupChat, GroupChatManager

from src.llm.gates.azure_anthropic_gate import AzureAnthropicGateFactory
from src.llm.gates.ollama_gate import OllamaGateFactory
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession
from autogen.mcp import create_toolkit

from src.utilities.telemetry.telemetry import Telemetry
from src.utilities.telemetry.trace_provider import TraceProvider

async def update_testcase(user_prompt: str, testCaseJSON: str):
    ollama_config = OllamaGateFactory(
            model_name="gemma4:31b"
        ).build()
    
    #azure_config = AzureAnthropicGateFactory(model_name="claude-opus-4-6").build()
    async with (streamable_http_client("http://127.0.0.1:8000/mcp") as (read, write, _), ClientSession(read, write) as session,):
        await session.initialize()
        #tracer_provider = TraceProvider.set_trace_provider()
        #Telemetry.setup(tracer_provider=tracer_provider, capture_messages=True)
        toolkit = await create_toolkit(session=session)
        await session.call_tool("load_testcase", arguments={"testcaseAsString": testCaseJSON})

        agent = ConversableAgent(
            name="agent",
            system_message=(
                "You are an expert test designer. You modify testcases using MCP tool calls.\n"
                "IMPORTANT: You MUST use tool calls to interact with the testcase.\n"
                "1. First call 'get_current_testcase' to see the current state.\n"
                "2. Then use the appropriate MCP tools to make changes.\n"
                "Never write code. Always use the provided tool calls."
            ),
            llm_config=ollama_config,
            human_input_mode="NEVER"
        )

        toolkit.register_for_llm(agent)

        toolcall_curator = ConversableAgent(
            name="critic",
            system_message="Other agents will request some toolcalls, but are not formatting them correctly for tool execution. Format it accordingly, so the MCP server can execute the tool call.",
            llm_config=ollama_config
        )
        toolkit.register_for_llm(toolcall_curator)

        tool_executor = ConversableAgent(
            name="tool_executor",
            system_message="You execute tool calls. Do not generate responses.",
            llm_config=False,
            human_input_mode="NEVER"

        )
        toolkit.register_for_execution(tool_executor)

        planning_chat = GroupChat(
            agents=[agent, toolcall_curator, tool_executor],
            max_round=3,
            speaker_selection_method="auto"
        )
        manager = GroupChatManager(groupchat=planning_chat, llm_config=ollama_config)

        result = await agent.a_initiate_chat(manager, message=user_prompt)
        print(result)