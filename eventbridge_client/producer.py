import boto3
import json
from botocore.exceptions import ClientError
from jsonschema import validate


class EventProducer:
    def __init__(self, region_name="us-east-1"):
        self.eventbridge = boto3.client("events", region_name=region_name)
        self.schemas = boto3.client("schemas", region_name=region_name)

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
            print(f"Error producing event: {e}")
            raise

    def _validate_event(self, detail, schema_name):
        try:
            schema_response = self.schemas.describe_schema(SchemaName=schema_name)
            schema = json.loads(schema_response["Content"])
            validate(instance=detail, schema=schema)
        except ClientError as e:
            print(f"Error fetching schema: {e}")
            raise
        except Exception as e:
            print(f"Error validating event against schema: {e}")
            raise
