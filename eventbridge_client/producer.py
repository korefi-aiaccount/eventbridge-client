import boto3
import json
from botocore.exceptions import ClientError
from jsonschema import validate
import logging
from .schema_registry import SchemaRegistry

logger = logging.getLogger(__name__)


class EventProducer:
    def __init__(self, registry_type, registry_url=None, region_name="us-east-1"):
        self.eventbridge = boto3.client("events", region_name=region_name)
        self.schema_registry = SchemaRegistry(registry_type, registry_url, region_name)

    def produce(self, event_bus_name, event_source, detail_type, detail, schema_name):
        self._validate_event(detail, schema_name)

        try:
            response = self.eventbridge.put_events(
                Entries=[
                    {
                        "Source": event_source,
                        "DetailType": detail_type,
                        "Detail": json.dumps(detail),
                        "EventBusName": event_bus_name,
                    }
                ]
            )
            return response
        except ClientError as e:
            logger.error(f"Error producing event: {e}")
            raise

    def _validate_event(self, detail, schema_name):
        try:
            schema = self.schema_registry.get_schema(schema_name)
            validate(instance=detail, schema=schema)
        except Exception as e:
            logger.error(f"Error validating event against schema: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize the EventProducer with the desired registry type
    # Configuration
    SCHEMA_REGISTRY_URL = "http://localhost:8080"
    SCHEMA_ID = "FileUploaded-v0"

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

    try:
        response = producer.produce(
            event_bus_name, event_source, detail_type, detail, schema_name
        )
        print(f"Event produced successfully: {response}")
    except Exception as e:
        print(f"Failed to produce event: {e}")
