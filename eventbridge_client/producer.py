import boto3
import json
from botocore.exceptions import ClientError
from jsonschema import validate
import logging
from .schema_registry import SchemaRegistry
from typing import Any, Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EventProducer:
    def __init__(
        self,
        schema_registry: SchemaRegistry,
        boto3_session: boto3.Session,
        endpoint_url: str = None,
    ):
        """
        Initialize the EventProducer.

        :param schema_registry: An instance of SchemaRegistry used to fetch and validate event schemas.
        :param boto3_session: A boto3 session object with AWS credentials and configuration.
        :param endpoint_url: Optional custom endpoint URL for the EventBridge client.
        """
        # Extract AWS credentials from boto3 session
        credentials = boto3_session.get_credentials()
        self.aws_access_key_id = credentials.access_key
        self.aws_secret_access_key = credentials.secret_key
        self.aws_session_token = credentials.token

        client_kwargs = {
            "region_name": boto3_session.region_name,
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
        }

        self.endpoint_url = endpoint_url

        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        if self.aws_session_token:
            client_kwargs["aws_session_token"] = self.aws_session_token

        self.eventbridge = boto3.client("events", **client_kwargs)

        self.schema_registry = schema_registry

    def produce(
        self,
        event_bus_name: str,
        event_source: str,
        detail_type: str,
        detail: Dict[str, Any],
        schema_name: str,
    ) -> Dict[str, Any]:
        """
        Produce an event to the specified EventBridge event bus.

        :param event_bus_name: The name of the EventBridge event bus.
        :param event_source: The source of the event.
        :param detail_type: The type of detail in the event.
        :param detail: The event detail as a dictionary.
        :param schema_name: The name of the schema to validate the event detail against.
        :return: The response from the EventBridge put_events API call.
        """
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
            logger.info(f"Event produced successfully: {response}")
            return response
        except ClientError as e:
            logger.error(f"Error producing event: {e}")
            raise

    def _validate_event(self, detail: Dict[str, Any], schema_name: str) -> None:
        """
        Validate the event detail against the specified schema.

        :param detail: The event detail as a dictionary.
        :param schema_name: The name of the schema to validate the event detail against.
        :raises: Exception if the event detail does not conform to the schema.
        """
        try:
            schema = self.schema_registry.get_schema(schema_name)
            validate(instance=detail, schema=schema)
            logger.debug(f"Event validated successfully against schema: {schema_name}")
        except Exception as e:
            logger.error(f"Error validating event against schema: {e}")
            raise


# Example usage
if __name__ == "__main__":

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
