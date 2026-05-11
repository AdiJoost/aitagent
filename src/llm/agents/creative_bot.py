from autogen import ConversableAgent, LLMConfig
from autogen.opentelemetry import instrument_agent


class CreativeBot:

    DEFAULT_SYSTEM_MESSAGE="""
    You are an helpful assistant that is tasked with comming up with some date ideas. You will be given some parameters about the date. When you need to research the internet, state what you want to research and ask for the internetbot to do so.
    """

    DEFAULT_DESCRIPTION="""
    The creative bot is able to create some nice date ideas. However, she does not know, what activities are actually possible on her own and needs a research first.
    """

    def __init__(self, llm_config: LLMConfig, name: str=None, system_message: str=None, tracer_provider=None, description: str=None):
        self.llm_config = llm_config
        self._system_message= system_message if system_message else self.DEFAULT_SYSTEM_MESSAGE
        self._name = name if name else str(self.__class__)
        self._tracer_provider = tracer_provider
        self._description = description if description else self.DEFAULT_DESCRIPTION

    def build(self) -> ConversableAgent:
        creative_agent = ConversableAgent(
            name=self._name,
            system_message=self._system_message,
            llm_config=self.llm_config,
            description=self._description
        )
        if self._tracer_provider:
            instrument_agent(creative_agent, tracer_provider=self._tracer_provider)
        return creative_agent