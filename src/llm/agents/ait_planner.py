import random
from typing import List

from autogen import AssistantAgent, LLMConfig
from autogen.opentelemetry import instrument_agent

from src.llm.agents.tool_registry import ToolExecutor


class AITPlannerAgent():

    DEFAULT_SYSTEM_MESSAGE="""
        You are a planner that orchestrates a group of agents.

        Available agents:
        - user: answers questions
        - creative_agent: can select tools to call
        """
    
    DEFAULT_DESCRIPTION="""
    The Planner is responsible for choosing the next agent to speak.
    """

    ENFORCE_OUTPUT ="""
        Only output the name of the next agent to speak.
        Valid options: $
        Do NOT explain.
        """

    def __init__(self, llm_config: LLMConfig, agent_names: List[str], tool_executor:ToolExecutor, name: str=None, system_message: str=None, tracer_provider=None, description: str= None):
        self.llm_config = llm_config
        self._agent_names = agent_names
        self._system_message= system_message if system_message else self.DEFAULT_SYSTEM_MESSAGE
        self._name = name if name else str(self.__class__)
        self._tracer_provider = tracer_provider
        self._description = description if description else self.DEFAULT_DESCRIPTION
        self._guardrail = self.ENFORCE_OUTPUT.replace("$", ", ".join(name for name in agent_names))
        self.tool_executor = tool_executor
        self.validation_done = False
        self.internet_research_done=False
        self._assistant = self.build()

    def build(self) -> AssistantAgent:
        planner = AssistantAgent(
            name=self._name,
            system_message=self._system_message,
            llm_config=self.llm_config,
            description=self._description
        )
        if self._tracer_provider:
            instrument_agent(planner, tracer_provider=self._tracer_provider)
        return planner

    def extract_tool_calls(self, message: dict):
        if not isinstance(message, dict):
            return None
        
        tool_calls = message.get("tool_calls")
        
        # Debug: Log the message structure to understand what's being returned
        print(f"DEBUG - Message keys: {message.keys()}")
        print(f"DEBUG - Message content: {message.get('content', '')}")
        print(f"DEBUG - Tool calls found: {tool_calls}")
        if message.get("content"):
            print(f"DEBUG - Content length: {len(message.get('content', ''))}")
        
        return tool_calls
        
    def _planner_selection(self, last_speaker, groupchat):
        messages = groupchat.messages.copy()

        last_message = groupchat.messages[-1]

        tool_calls = self.extract_tool_calls(last_message)

        if tool_calls:
            print("Toolcall detected")
            return self.tool_executor 
        messages.append({
            "role":"system",
            "content": f"Validation was completed {last_speaker}"
        })
        messages.append({
            "role": "system",
            "content": self._guardrail
        })
        response = self._assistant.generate_reply(
            messages=messages,
            sender=None
        )
        print(f"Planner Response: {response}")
        if isinstance(response, dict):
            next_speaker_name = response.get("content", "").strip().lower()
        else:
            next_speaker_name = str(response).strip().lower()

        for agent in groupchat.agents:
            if agent.name.strip().lower() == next_speaker_name:
                return agent
        for agent in groupchat.agents:
            if agent.name.strip().lower() == "creative_agent":
                return agent
        return random.choice(groupchat.agents)
    
    def planner_selection(self, last_speaker, groupchat):
        messages = groupchat.messages.copy()

        last_message = groupchat.messages[-1]
        
        if "Validation complete" in last_message.get("content", ""):
            self.validation_done = True

        tool_calls = self.extract_tool_calls(last_message)

        if tool_calls:
            print("✓ Toolcall detected - routing to tool_executor")
            return self.tool_executor
        
        # If message is empty but has tool_calls structure, also route to tool_executor
        if (last_message.get("content", "").strip() == "" or not last_message.get("content")) and last_message.get("tool_calls"):
            print("✓ Empty content with tool_calls detected - routing to tool_executor")
            return self.tool_executor
        
        messages.append({
            "role": "system",
            "content": self._guardrail
        })

        response = self._assistant.generate_reply(
            messages=messages,
            sender=None
        )

        print(f"Planner Response: {response}")

        if isinstance(response, dict):
            next_speaker_name = response.get("content", "").strip().lower()
        else:
            next_speaker_name = str(response).strip().lower()

        next_agent = self.findAgentByName(next_speaker_name, groupchat)
        return next_agent if next_agent else self.findAgentByName("creative_agent", groupchat)
    
    def isValidatorBot(self, name):
        return name.strip().lower() == "validatorbot"
    
    def findAgentByName(self, name, groupchat):
        for agent in groupchat.agents:
                if agent.name.strip().lower() == name:
                    return agent
        return None