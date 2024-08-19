# EventBridge Client

This is a simple EventBridge client for producing and consuming events.

## Installation

To install the package, you can use pip:

```
pip install git+https://bitbucket.org/credit-application/eventbridge-client@<<stable-tagged>>
```

Please add latest stable version in `<<stable-tagged>>`

## Usage

### Producer

```python
from eventbridge_client.producer import EventProducer

# Configuration
SCHEMA_REGISTRY_URL = "http://localhost:8080"
SCHEMA_ID = "FileUploaded-v0"

# Initialize the EventProducer with the desired registry type
producer = EventProducer(
    registry_type="apicurio",
    registry_url=SCHEMA_REGISTRY_URL,
)

# Example event details
event_bus_name = "my-event-bus"
event_source = "my-application"
detail_type = SCHEMA_ID
detail = {
    "user_id": "12345",
    "email": "user@example.com",
    "signup_date": "2024-03-15T10:30:00Z",
}
schema_name = SCHEMA_ID

# Produce the event
try:
    response = producer.produce(
        event_bus_name, event_source, detail_type, detail, schema_name
    )
    print(f"Event produced successfully: {response}")
except Exception as e:
    print(f"Failed to produce event: {e}")
```

### Consumer

Example 1

```Python
    # Set environment variables
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_ENDPOINT_URL"] = "http://localhost:4566"

SQS_QUEUE_URL = "http://localhost:4566/000000000000/extraction-service-queue"
REGISTRY_TYPE = "apicurio"
SCHEMA_REGISTRY_URL = "http://localhost:8080"
SCHEMA_ID = "FileUploaded-v0"

async def process_message(message: Dict[str, Any]):
    print(f"Processing message: {message}")

async def run_consumer():
    schema_registry = SchemaRegistry(
        REGISTRY_TYPE, SCHEMA_REGISTRY_URL, "us-east-1"
    )
    consumer = SQSConsumer(
        queue_url=SQS_QUEUE_URL,
        poll_interval=30,
        schema_registry=schema_registry,
        schema_name=SCHEMA_ID,
        region_name="us-east-1",
    )
    await consumer.start(process_message)

# Run the consumer
asyncio.run(run_consumer())
```

Example 2

```python
# Example usage:
async def process_message(message: Dict[str, Any]):
    # Implement your message processing logic here
    print(f"Processing message: {message}")


async def run_consumer():
    schema_registry = SchemaRegistry(
        "your_registry_type", "your_registry_url", "your_region"
    )
    consumer = SQSConsumer(
        queue_url="your_sqs_queue_url",
        schema_registry=schema_registry,
        schema_name="your_schema_name",
        region_name="your_aws_region",
    )
    await consumer.start(process_message)


# For FastAPI
from fastapi import FastAPI

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_consumer())


# For Django (in your app's ready() method)
import django
from django.apps import AppConfig


class YourAppConfig(AppConfig):
    name = "your_app_name"

    def ready(self):
        if not django.conf.settings.DEBUG:
            asyncio.run(run_consumer())
```
