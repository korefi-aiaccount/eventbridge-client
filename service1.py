import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.propagators.aws import AwsXRayPropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")

# Set up tracer provider
provider = TracerProvider()
processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Get a tracer
tracer = trace.get_tracer(__name__)

# Create a span
with tracer.start_as_current_span("service-1-span") as span:
    # Do some work...
    span.set_attribute("service", "service-1")


    # Get the current context and serialize it
    propagator = TraceContextTextMapPropagator()
    carrier = {}
    propagator.inject(carrier)

    # Write context to file
    with open("context.txt", "w") as f:
        for key, value in carrier.items():
            f.write(f"{key}: {value}\n")

print("Service 1 completed")
