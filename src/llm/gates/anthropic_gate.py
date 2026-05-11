import os

from autogen import LLMConfig


class AnthropicGateFactory():

    def __init__(self, model_name: str ="claude-sonnet-4-6"):
        self.api_key = os.environ["ANTHROPIC_API_KEY"]
        self.model_name = model_name

    def build(self) -> LLMConfig:
        return LLMConfig({
            "model": self.model_name,
            "api_type": "anthropic",
            "api_key": os.getenv("ANTHROPIC_API_KEY") 
        })