from autogen import ConversableAgent, LLMConfig
from autogen.opentelemetry import instrument_agent
from autogen.tools.experimental import SearxngSearchTool


class InternetSearcher:

    DEFAULT_SYSTEM_MESSAGE="""
    You are an helpful assistant that is tasked with searching the internet for information about possible date activities such as restaurants, events, and entertainment options. Based on the messages above and the request of the other agents, think about what you want to research in the internet.
    """

    DEFAULT_DESCRIPTION="""
    The InternetBot can research activities in the city or nearby depending on what the parameters for the date are.
    """

    def __init__(self, llm_config: LLMConfig, name: str=None, system_message: str=None, tracer_provider=None, description: str=None):
        self.llm_config = llm_config
        self._system_message= system_message if system_message else self.DEFAULT_SYSTEM_MESSAGE
        self._name = name if name else str(self.__class__)
        self._tracer_provider = tracer_provider
        self._description = description if description else self.DEFAULT_DESCRIPTION

    def build(self) -> ConversableAgent:
        internet_searcher_agent = ConversableAgent(
            name=self._name,
            system_message=self._system_message,
            llm_config=self.llm_config,
        )
        search_tool = SearxngSearchTool()
        search_tool.register_tool(internet_searcher_agent)
        if self._tracer_provider:
            instrument_agent(internet_searcher_agent, tracer_provider=self._tracer_provider)
        return internet_searcher_agent