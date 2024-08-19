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
SCHEMA_REGISTRY_URL = "http://localhost:8080"
SCHEMA_ID = "FileUploaded-v0"
REGISTRY_TYPE = "apicurio"

AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"
AWS_ENDPOINT_URL = "http://localhost:4566"

boto3_session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name="us-east-1",
)

schema_registry = SchemaRegistry(REGISTRY_TYPE, SCHEMA_REGISTRY_URL)
producer = EventProducer(
    schema_registry=schema_registry,
    boto3_session=boto3_session,
    endpoint_url="http://localhost:4566",
)

# Example event details
event_bus_name = "my-event-bus"
event_source = "my-application"
detail_type = SCHEMA_ID
detail = {
    "event_type": "FileUploaded-v0",
    "version": "0.1.0",
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "time": "2024-08-16T10:30:00Z",
    "data": {
        "file_id": "98765432-abcd-efgh-ijkl-123456789012",
        "file_url": "https://my-bucket.s3.amazonaws.com/path/to/file.pdf",
        "user_ccm": "11112222-3333-4444-5555-666677778888",
        "company_uuid": "aaaabbbb-cccc-dddd-eeee-ffff00001111",
        "doc_metadata": {
            "doc_type": "bank_statement",
            "bank_name": "Example Bank",
            "account_number": "1234567890",
            "file_type": "STMT",
        },
        "status": "EXTRACTION",
    },
    "trace_context": {
        "trace_id": "1-581cf771-a006649127e371903a2de979",
        "span_id": "b9c7c989f97918e1",
        "parent_span_id": "def456",
        "sampled": "1",
    },
    "idempotency_key": "87654321-hgfe-dcba-4321-123456789012",
}
schema_name = SCHEMA_ID

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
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"
AWS_ENDPOINT_URL = "http://localhost:4566"

SQS_QUEUE_URL = "http://localhost:4566/000000000000/extraction-service-queue"
REGISTRY_TYPE = "apicurio"
SCHEMA_REGISTRY_URL = "http://localhost:8080"
SCHEMA_ID = "FileUploaded-v0"

boto3_session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name="us-east-1",
)

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
        boto3_session=boto3_session,
        endpoint_url="http://localhost:4566",
    )
    await consumer.start(process_message)

# Run the consumer
asyncio.run(run_consumer())
```

Run on FastAPI Server

```python
# FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_consumer()
    yield
```
