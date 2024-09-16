import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.propagators.aws import AwsXRayPropagator
from opentelemetry.sdk.extension.aws.trace import AwsXRayIdGenerator
from opentelemetry.propagate import set_global_textmap
from typing import Any, Dict
import functools

_tracer = None
_propagator = None


def setup_tracing(
    service_name: str, jaeger_host: str = "localhost", jaeger_port: int = 6831
):
    global _tracer, _propagator
    if _tracer is None or _propagator is None:
        BotocoreInstrumentor().instrument()

        use_xray = os.environ.get("USE_XRAY", "false").lower() == "true"

        resource = Resource(attributes={ResourceAttributes.SERVICE_NAME: service_name})

        id_generator = AwsXRayIdGenerator() if use_xray else None
        tracer_provider = TracerProvider(resource=resource, id_generator=id_generator)

        if use_xray:
            otlp_exporter = OTLPSpanExporter(
                endpoint="https://xray.us-east-1.amazonaws.com"
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            _propagator = AwsXRayPropagator()
        else:
            jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_host, agent_port=jaeger_port
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
            _propagator = TraceContextTextMapPropagator()

        trace.set_tracer_provider(tracer_provider)
        set_global_textmap(_propagator)  # Corrected line

        _tracer = trace.get_tracer(__name__)

    return _tracer, _propagator


def inject_trace_context(propagator, detail: Dict[str, Any]) -> None:
    """Injects the current trace context into the event detail."""
    trace_context = {}
    propagator.inject(trace_context)
    detail["trace_context"] = trace_context


def trace_span(span_name):
    def decorator_trace_span(func):
        @functools.wraps(func)
        def wrapper_trace_span(self, *args, **kwargs):
            context = kwargs.get("context", {})
            with self.tracer.start_as_current_span(span_name, context):
                return func(self, *args, **kwargs)

        return wrapper_trace_span

    return decorator_trace_span


def extract_trace_context(get_detail: Dict[str, Any], propagator) -> Any:
    """Extracts the trace context from the message details."""
    trace_context = get_detail.get("trace_context", {})
    return propagator.extract(trace_context)
