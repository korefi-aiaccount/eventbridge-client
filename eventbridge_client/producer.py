import boto3
import json
import requests
from botocore.exceptions import ClientError
from jsonschema import validate
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class SchemaRegistry:
    def __init__(self, registry_type, url=None, region_name="us-east-1"):
        self.registry_type = registry_type
        self.url = url
        self.region_name = region_name
        if registry_type == "eventbridge":
            self.schemas = boto3.client("schemas", region_name=region_name)

    @lru_cache(maxsize=100)
    def get_schema(self, schema_id):
        if self.registry_type == "eventbridge":
            return self._get_eventbridge_schema(schema_id)
        elif self.registry_type == "apicurio":
            return self._get_apicurio_schema(schema_id)
        else:
            raise ValueError(f"Unsupported registry type: {self.registry_type}")

    def _get_eventbridge_schema(self, schema_name):
        try:
            schema_response = self.schemas.describe_schema(SchemaName=schema_name)
            return json.loads(schema_response["Content"])
        except ClientError as e:
            logger.error(f"Error fetching schema from EventBridge: {e}")
            raise

    def _get_apicurio_schema(self, schema_id):
        url = f"{self.url}/apis/registry/v2/groups/default/artifacts/{schema_id}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve schema from Apicurio: {e}")
            raise


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
    producer = EventProducer(registry_type="eventbridge", region_name="us-east-1")

    # Example event details
    event_bus_name = "my-event-bus"
    event_source = "my-application"
    detail_type = "user-signup"
    detail = {
        "user_id": "12345",
        "email": "user@example.com",
        "signup_date": "2024-03-15T10:30:00Z",
    }
    schema_name = "user-signup-schema"

    try:
        response = producer.produce(
            event_bus_name, event_source, detail_type, detail, schema_name
        )
        print(f"Event produced successfully: {response}")
    except Exception as e:
        print(f"Failed to produce event: {e}")
