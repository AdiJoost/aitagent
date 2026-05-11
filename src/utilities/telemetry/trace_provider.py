import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class TraceProvider:
    _trace_provider = None
    _DEFAULT_SERVICE_NAME = "eros-service"
    _DEFAULT_ENDPOINT = "http://localhost:4317"

    @classmethod
    def set_trace_provider(cls):
        if cls._trace_provider is not None:
            return cls._trace_provider
        
        service_name = os.getenv("TRACE_SERVICE_NAME", cls._DEFAULT_SERVICE_NAME)
        resource = Resource.create({"service.name": service_name})
        tracer_provider = TracerProvider(resource=resource)
        cls._trace_provider = tracer_provider

        endpoint = os.getenv("JAEGER_HOST", cls._DEFAULT_ENDPOINT)
        exporter = OTLPSpanExporter(endpoint=endpoint)
        tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(tracer_provider)
        return tracer_provider