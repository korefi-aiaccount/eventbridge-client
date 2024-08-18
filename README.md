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

### Consumer (TODO)
