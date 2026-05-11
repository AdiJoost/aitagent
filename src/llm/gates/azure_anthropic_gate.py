import os

from autogen import LLMConfig


class AzureAnthropicGateFactory():

    def __init__(self, model_name: str = "claude-opus-4-6"):
        self.model_name = model_name

    def build(self) -> LLMConfig:
        return LLMConfig({
            "model": self.model_name,
            "api_type": "anthropic",
            "api_key": os.getenv("AZURE_ANTHROPIC_API_KEY"),
            "base_url": os.getenv("AZURE_ANTHROPIC_ENDPOINT").rstrip("/"),
        })