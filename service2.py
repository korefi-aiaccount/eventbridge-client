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
from opentelemetry.propagate import set_global_textmap
import time


# Configure the resource with service name
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: "servicex-2",
})


# Configure OTLP exporter for service 2
otlp_exporter_2 = OTLPSpanExporter(endpoint="http://localhost:4317")

# Set up tracer provider for service 2
provider_2 = TracerProvider(resource=resource)
processor_2 = BatchSpanProcessor(otlp_exporter_2)
provider_2.add_span_processor(processor_2)
trace.set_tracer_provider(provider_2)

# Set global propagator
set_global_textmap(AwsXRayPropagator())

# Get a tracer for service 2
tracer_2 = trace.get_tracer(__name__)

def service_2_function():
    # Read context from file
    carrier = {}
    with open("context.txt", "r") as f:
        for line in f:
            key, value = line.strip().split(": ", 1)
            carrier[key] = value

    # Extract the context
    context = AwsXRayPropagator().extract(carrier)

    # Create a new span with the extracted context for service 2
    attributes = {
        "rpc.system": "aws-api",
        "rpc.service": "servicex-2",
        "rpc.method": "process",
    }
    with tracer_2.start_as_current_span("service-2-operation", context=context, attributes=attributes) as span:
        span.set_attribute("custom.attribute", "service-2-value")

        # Mock producer step
        producer_attributes = {
            "rpc.system": "aws-api",
            "rpc.service": "servicex-2",
            "rpc.method": "produce",
        }
        with tracer_2.start_as_current_span("service-2-producer", attributes=producer_attributes) as producer_span:
            producer_span.set_attribute("producer.action", "generate_data")
            # Simulate some work
            time.sleep(0.5)
            producer_span.add_event("Data generated")

        # Mock consumer step
        consumer_attributes = {
            "rpc.system": "aws-api",
            "rpc.service": "servicex-2",
        }
        with tracer_2.start_as_current_span("service-2-consumer", attributes=consumer_attributes) as consumer_span:
            consumer_span.set_attribute("consumer.action", "process_data")
            # Simulate some work
            time.sleep(0.7)
            consumer_span.add_event("Data processed")

        span.add_event("Service 2 operation completed")


service_2_function()
print("Service 2 completed")
