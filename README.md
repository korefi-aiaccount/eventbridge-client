# EventBridge Client

This is a simple EventBridge client for producing and consuming events.

## Installation

To install the package, you can use pip:

```
pip install git+https://github.com/yourusername/eventbridge_client.git
```

## Usage

### Producer

```python
from eventbridge_client.producer import EventProducer

producer = EventProducer()

event_detail = {"key": "value"}
response = producer.produce(
    event_bus_name="my-event-bus",
    event_source="my-source",
    detail_type="MyEventType",
    detail=event_detail,
    schema_name="MySchemaName"
)
print(f"Event produced: {response}")
```

### Consumer

```python
import logging
from eventbridge_client.consumer import EventConsumer

# For EventBridge Schema Registry
schema_registry = SchemaRegistry('eventbridge', region_name='us-east-1')
# For Apicurio Registry
# schema_registry = SchemaRegistry('apicurio', url='https://your-apicurio-url.com')

consumer = EventConsumer(
    queue_url="https://sqs.us-east-1.amazonaws.com/123456789012/my-queue",
    schema_registry=schema_registry,
    schema_id="MySchemaName"  # or Schema ID for Apicurio
)

while True:
    try:
        msg = consumer.poll(1.0)
        logger.info("Pulling...")
        if msg is None:
            continue

        # Validate and process the message
        if process_msg(msg):
            msg.commit()
            logger.info("Message processed and committed successfully")
        else:
            logger.warning("Failed to process message, not committing")

    except Exception as e:
        logger.error(f"Unknown error: {e}")
```

Make sure to set up your AWS credentials in your environment or configuration file before using this client.
