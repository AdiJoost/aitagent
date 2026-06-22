import os

from autogen import LLMConfig


class OllamaGateFactory():

    def __init__(self, model_name: str, stream: bool = False, tool_choice: str = "auto"):
        self.ollama_host = os.environ["OLLAMA_HOST"]
        self.model_name = model_name
        self.stream = stream
        self.tool_choice = tool_choice

    def build(self) -> LLMConfig:
        return LLMConfig({
            "model": self.model_name,
            "api_type": "ollama",
            "stream": self.stream,
            "client_host": self.ollama_host,
            "tool_choice": self.tool_choice
        })