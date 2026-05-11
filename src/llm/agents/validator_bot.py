from autogen import ConversableAgent, LLMConfig
from autogen.opentelemetry import instrument_agent


class ValidatorBot:

    DEFAULT_SYSTEM_MESSAGE="""
    The group is trying to plan a date. You are task to validate, that all parameters for the date are clear.
    The parameters are:
    What city? How long should the date be? When will the date take place? How many people are attending? How expensive could the activities be? How does the group commute?
    You are free to extend these parameters. Also you are the judge, whether some parameters can be left unanswered or need to be explizitly mentioned.
    If you need some clearifying parameters, ask for userinput. If not, ask for the continue planning.
    - Ask at most 2 clarifying questions
    - If enough info is available, stop asking and say "Validation complete"
    Only answere with: Please ask the user: (your questions here), or answere with "Validation complete" Do not explain yourself
    """

    DEFAULT_DESCRIPTION="""
    The Validatorbot is responsible for checking, that all parameters about the Date are clear.
    """

    def __init__(self, llm_config: LLMConfig, name: str=None, system_message: str=None, tracer_provider=None, description: str= None):
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