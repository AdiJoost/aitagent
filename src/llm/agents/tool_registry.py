
from autogen import ConversableAgent, LLMConfig
from autogen.opentelemetry import instrument_agent
from autogen.tools.experimental import SearxngSearchTool


class ToolExecutor:

    DEFAULT_DESCRIPTION="""
    This Agent is only there for executing tool calls.
    """

    def __init__(self, llm_config: LLMConfig, name: str=None, tracer_provider=None, description: str=None):
        self.llm_config = llm_config
        self._system_message= ""
        self._name = name if name else str(self.__class__)
        self._tracer_provider = tracer_provider
        self._description = description if description else self.DEFAULT_DESCRIPTION

    def build(self) -> ConversableAgent:
        internet_searcher_agent = ConversableAgent(
            name=self._name,
            system_message=self._system_message,
            llm_config=self.llm_config,
        )
        if self._tracer_provider:
            instrument_agent(internet_searcher_agent, tracer_provider=self._tracer_provider)
        return internet_searcher_agent