from autogen import AssistantAgent, GroupChat, GroupChatManager, UserProxyAgent
from autogen.mcp import create_toolkit
from autogen.opentelemetry import instrument_agent, instrument_llm_wrapper
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter,
                                            SimpleSpanProcessor)

from src.llm.agents.ait_planner import AITPlannerAgent
from src.llm.agents.creative_bot import CreativeBot
from src.llm.agents.internet_searcher import InternetSearcher
from src.llm.agents.planner import PlannerAgent
from src.llm.agents.tool_registry import ToolExecutor
from src.llm.agents.validator_bot import ValidatorBot
from src.llm.gates.ollama_gate import OllamaGateFactory
from src.llm.prompts.creative_agent_html_description import (
    html_description, thinker_bot_system_message)
from src.llm.prompts.testcase import miniscule_testcase
from src.utilities.mcp.mcp_toolkit import MCPToolkit
from src.utilities.telemetry.telemetry import Telemetry
from src.utilities.telemetry.trace_provider import TraceProvider


async def tryin():
    ollama_config = OllamaGateFactory(
            model_name="gemma4:31b"
        ).build()
    async with (streamable_http_client("http://127.0.0.1:8000/mcp") as (read, write, _), ClientSession(read, write) as session,):
        await session.initialize()
        tracer_provider = TraceProvider.set_trace_provider()
        Telemetry.setup(tracer_provider=tracer_provider, capture_messages=True)
        

        toolkit = await create_toolkit(session=session, use_mcp_resources=False)
        
        creative_agent = CreativeBot(
            llm_config=ollama_config,
            name="creative_agent",
            system_message=f"{thinker_bot_system_message}{html_description}",
            tracer_provider=tracer_provider
        ).build()

        user_proxy = UserProxyAgent(
            name="user",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
        )

        tool_executor = ToolExecutor(
            llm_config=ollama_config,
            name="tool_executor",
            tracer_provider=tracer_provider
        ).build()

        toolkit.register_for_llm(creative_agent)
        toolkit.register_for_execution(tool_executor)

        planner = AITPlannerAgent(
            llm_config=ollama_config,
            agent_names= ["creative_agent", "user"],
            tool_executor=tool_executor,
            name="PlannerBot",
            tracer_provider=tracer_provider
        )

        groupchat = GroupChat(
        agents=[creative_agent, user_proxy, tool_executor],
        messages=[],
        max_round=20,
        speaker_selection_method=planner.planner_selection
        )
        manager = GroupChatManager(groupchat=groupchat, llm_config=ollama_config)

        await user_proxy.a_initiate_chat(
            manager,
            message=f"You have a testcase with the following testsections {miniscule_testcase}. " +
                    "Change the name of the first two sections to section 1 and section 2. " +
                    "Use the tools given to create a tasklist first.",
        )

async def generate_ne_names():
    ollama_config = OllamaGateFactory(model_name="llama3.1:8b").build()

    async with (
        streamable_http_client("http://127.0.0.1:8000/mcp") as (read, write, _),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        toolkit = await create_toolkit(session=session, use_mcp_resources=False)

        creative_agent = AssistantAgent(
            name="creative_agent",
            llm_config=ollama_config,
            code_execution_config=False,
        )

        toolkit.register_for_llm(creative_agent)

        test_section= """
            "testSectionDTOList": [
                {
                    "changeDate": "2023-02-06T14:46:53.409Z",
                    "descriptionGerman": "",
                    "dbId": 910,
                    "released": false,
                    "inspectionType": "FULL_AND_PARTIAL_TEST",
                    "createDate": "2023-02-03T18:14:21.783Z",
                    "state": "ENABLED",
                    "testElementDTOList": [],
                    "title": "<!--(DescriptionHead) Timing Values",
                    "titleType": "STANDARD",
                    "parameters": { "parameters": [], "rows": [] }
                },
                {
                    "changeDate": "2023-02-06T14:46:53.409Z",
                    "descriptionGerman": "",
                    "dbId": 911,
                    "released": false,
                    "inspectionType": "FULL_AND_PARTIAL_TEST",
                    "createDate": "2023-02-03T18:14:21.783Z",
                    "state": "ENABLED",
                    "testElementDTOList": [],
                    "title": "(DescriptionBody)",
                    "titleType": "STANDARD",
                    "parameters": { "parameters": [], "rows": [] }
                },
                ]"""

        result = await creative_agent.a_run(
            message=f"You have a testcase with the following testsections {test_section}. Change the name of both sections to section 1 and section 2. Then tell me what they are called now. Use the MCP_tools for renaming",
            tools=toolkit.tools,
            max_turns=3,
            user_input=False,
        )

        await result.process()
        print(result.messages)