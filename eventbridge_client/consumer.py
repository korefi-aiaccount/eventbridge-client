import asyncio
from typing import Callable, Dict, Any
import boto3
from botocore.exceptions import ClientError
from jsonschema import validate

from .tracing import extract_trace_context, setup_tracing
from .schema_registry import SchemaRegistry
import logging
import json


class SQSConsumer:
    def __init__(
        self,
        queue_url: str,
        schema_registry: SchemaRegistry,
        schema_name: str,
        boto3_session: boto3.Session,
        poll_interval: float = 1.0,
        visibility_timeout: int = 30,
        max_messages: int = 1,
        wait_time: int = 20,
        processing_timeout: float = 5.0,
        endpoint_url: str = None,
        event_source: str = "unknown",
        tracing_host: str = "localhost",
        tracing_port: int = 6831,
    ):
        """
        Initialize the SQSConsumer.

        :param queue_url: URL of the SQS queue.
        :param schema_registry: Schema registry instance.
        :param schema_name: Name of the schema to validate messages against. Must be a valid schema name present in the schema registry.
        :param boto3_session: Boto3 session for AWS credentials.
        :param poll_interval: Interval between polling the SQS queue. Should be a positive float, recommended between 0.1 and 60.0 seconds.
        :param visibility_timeout: Visibility timeout for SQS messages.
                                   The period during which a message is invisible to other consumers after being retrieved from the queue.
                                   Must be an integer between 0 and 43200 (12 hours).
                                   Should be long enough to allow the message to be processed but short enough to reappear if processing fails.
        :param max_messages: Maximum number of messages to retrieve per poll. Must be an integer between 1 and 10.
        :param wait_time: Wait time for long polling. Must be an integer between 0 and 20 seconds.
        :param processing_timeout: Timeout for processing a single message.
                                   The maximum time allowed for processing a single message.
                                   Should be a positive float, recommended to be less than the visibility timeout to ensure the message is processed before it becomes visible again.
        :param endpoint_url: Custom endpoint URL for SQS. Must be a valid URL or None for default endpoint.
        """
        self.queue_url = queue_url
        self.schema_registry = schema_registry
        self.schema_name = schema_name
        self.poll_interval = poll_interval
        self.visibility_timeout = visibility_timeout
        self.max_messages = max_messages
        self.wait_time = wait_time
        self.processing_timeout = processing_timeout
        self.is_running = False
        self.schema = self.schema_registry.get_schema(self.schema_name)
        self.endpoint_url = endpoint_url
        self.boto3_session = boto3_session
        self.event_source = event_source

        # Set up tracing
        self.tracer, self.propagator = setup_tracing(
            self.event_source, tracing_host, tracing_port
        )

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize SQS client
        self.sqs_client = self._create_sqs_client()

    def _create_sqs_client(self):
        """
        Create an SQS client using the boto3 session.

        :return: Boto3 SQS client.
        """
        self.logger.info("Initializing SQS client with:")
        self.logger.info(f"  Region: {self.boto3_session.region_name}")
        self.logger.info(f"  Endpoint URL: {self.endpoint_url}")

        client_kwargs = {}
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        return self.boto3_session.client("sqs", **client_kwargs)

    async def _process_and_delete_message(
        self,
        message: Dict[str, Any],
        process_message: Callable[[Dict[str, Any]], None],
    ):
        """
        Process and delete a single SQS message.

        :param message: The SQS message to process.
        :param process_message: Callable to process the message.
        """
        body = message["Body"]
        body_dict = json.loads(body)
        get_detail = body_dict["detail"]
        span_name = str(body_dict["detail-type"])
        attributes = {
            "rpc.system": "aws-api",
            "rpc.service": self.event_source,
            "rpc.method": "Validate",
        }

        with self.tracer.start_as_current_span(span_name, attributes=attributes):
            validate(instance=get_detail, schema=self.schema)

        attributes.update({"rpc.method": "Process"})

        with self.tracer.start_as_current_span(span_name, attributes=attributes):
            await asyncio.wait_for(
                process_message(body),
                timeout=self.processing_timeout,
            )

        self.sqs_client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )
        self.logger.info("Message processed and deleted from queue")

    async def start(self, process_message: Callable[[Dict[str, Any]], None]):
        """
        Start the SQS consumer.

        :param process_message: Callable to process each message.
        """
        self.is_running = True

        while self.is_running:
            try:
                self.logger.info(f"Polling SQS queue: {self.queue_url}")
                response = self.sqs_client.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=self.max_messages,
                    WaitTimeSeconds=self.wait_time,
                    VisibilityTimeout=self.visibility_timeout,
                )

                messages = response.get("Messages", [])
                self.logger.info(f"Received {len(messages)} messages")

                for message in messages:
                    try:
                        body = message["Body"]
                        body_dict = json.loads(body)
                        get_detail = body_dict["detail"]

                        # Extract the trace context from the message attributes
                        context = extract_trace_context(get_detail, self.propagator)
                        attributes = {
                            "rpc.system": "aws-api",
                            "rpc.service": self.event_source,
                            "rpc.method": "Consume",
                        }
                        span_name = str(body_dict["detail-type"])
                        with self.tracer.start_as_current_span(
                            span_name, context, attributes=attributes
                        ):
                            await self._process_and_delete_message(
                                message, process_message
                            )
                    except asyncio.TimeoutError:
                        self.logger.error(
                            f"Message processing timed out after {self.processing_timeout} seconds"
                        )
                    except Exception as e:
                        self.logger.error(f"Error processing message: {str(e)}")

            except ClientError as e:
                self.logger.error(f"Error receiving messages: {str(e)}")
                if "InvalidClientTokenId" in str(e):
                    self.logger.error(
                        "Invalid AWS credentials. Please check your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
                    )
                    break

            await asyncio.sleep(self.poll_interval)

    def stop(self):
        """
        Stop the SQS consumer.
        """
        self.is_running = False


# Example usage
if __name__ == "__main__":

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
