from autogen.opentelemetry import instrument_llm_wrapper


class Telemetry:
    _configured = False

    @classmethod
    def setup(cls, tracer_provider, capture_messages: bool = True):
        if cls._configured:
            return
        instrument_llm_wrapper(
            tracer_provider=tracer_provider,
            capture_messages=capture_messages,
        )
        cls._configured = True