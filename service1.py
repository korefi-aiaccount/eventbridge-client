import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.propagators.aws import AwsXRayPropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.propagate import set_global_textmap


# Configure the resource with service name
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: "servicex-1",
})


# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")

# Set up tracer provider
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Set global propagator
set_global_textmap(AwsXRayPropagator())

# Get a tracer
tracer = trace.get_tracer(__name__)

def service_1_function():
    attributes = {
      "rpc.system": "aws-api",
      "rpc.service": "servicex-1",
      "rpc.method": "produce",
    }
    with tracer.start_as_current_span("service-1-operation", attributes=attributes) as span:
        # Do some work...
        span.set_attribute("custom.attribute", "service-1-value")

        # Get the current context and serialize it
        carrier = {}
        AwsXRayPropagator().inject(carrier)

        # Write context to file
        with open("context.txt", "w") as f:
            for key, value in carrier.items():
                f.write(f"{key}: {value}\n")


service_1_function()
print("Service 1 completed")
