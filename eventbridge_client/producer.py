import boto3
import json
from botocore.exceptions import ClientError
from jsonschema import validate
import logging
from .schema_registry import SchemaRegistry
from typing import Any, Dict
from .tracing import inject_trace_context, setup_tracing
from opentelemetry import trace

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EventProducer:
    def __init__(
        self,
        schema_registry: SchemaRegistry,
        boto3_session: boto3.Session,
        event_source: str = "unknown",
        endpoint_url: str = None,
        tracing_host: str = "localhost",
        tracing_port: int = 6831,
    ):
        """
        Initialize the EventProducer.

        :param schema_registry: An instance of SchemaRegistry used to fetch and validate event schemas.
        :param boto3_session: A boto3 session object with AWS credentials and configuration.
        :param endpoint_url: Optional custom endpoint URL for the EventBridge client.
        """
        self.schema_registry = schema_registry
        self.endpoint_url = endpoint_url
        self.event_source = event_source

        # Set up tracing
        self.tracer, self.propagator = setup_tracing(
            self.event_source, tracing_host, tracing_port
        )

        # Create EventBridge client using the provided boto3 session
        client_kwargs = {}
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        self.eventbridge = boto3_session.client("events", **client_kwargs)

    def produce(
        self,
        event_bus_name: str,
        detail_type: str,
        detail: Dict[str, Any],
        schema_name: str,
    ) -> Dict[str, Any]:
        """
        Produce an event to the specified EventBridge event bus.

        :param event_bus_name: The name of the EventBridge event bus.
        :param detail_type: The type of detail in the event.
        :param detail: The event detail as a dictionary.
        :param schema_name: The name of the schema to validate the event detail against.
        :return: The response from the EventBridge put_events API call.
        """
        span_name = f"Produce {detail_type} Event"
        with self.tracer.start_as_current_span(
            "producer_wrapper", kind=trace.SpanKind.SERVER
        ):
            with self.tracer.start_as_current_span(span_name):
                with self.tracer.start_as_current_span(f"Validate {detail_type} Event"):
                    self._validate_event(detail, schema_name)

                try:
                    # Inject the current trace context into the detail
                    inject_trace_context(detail)

                    with self.tracer.start_as_current_span(f"Put {detail_type} Event"):
                        response = self.eventbridge.put_events(
                            Entries=[
                                {
                                    "Source": self.event_source,
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
