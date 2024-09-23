import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.propagators.aws import AwsXRayPropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context import Context
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes


# Configure the resource with service name
resource = Resource.create({
    "service.name": "service-2"
})

# Configure OTLP exporter for service 2
otlp_exporter_2 = OTLPSpanExporter(endpoint="http://localhost:4317")

# Set up tracer provider for service 2
provider_2 = TracerProvider(resource=resource)
processor_2 = BatchSpanProcessor(otlp_exporter_2)
provider_2.add_span_processor(processor_2)
trace.set_tracer_provider(provider_2)

# Get a tracer for service 2
tracer_2 = trace.get_tracer(__name__)

# Read context from file
carrier = {}
with open("context.txt", "r") as f:
    for line in f:
        key, value = line.strip().split(": ", 1)
        carrier[key] = value

# Extract the context
propagator = TraceContextTextMapPropagator()
context = propagator.extract(carrier=carrier)

# Create a new span with the extracted context for service 2
with tracer_2.start_as_current_span("service-2-span", context=context) as span:
    # Do some work...
    span.set_attribute("custom.attribute", "service-2-value")

print("Service 2 completed")
