import asyncio
from typing import Callable, Dict, Any
import boto3
from botocore.exceptions import ClientError
from jsonschema import validate
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
        endpoint_url: str = None,  # Add endpoint_url as a parameter
    ):
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

        # Extract AWS credentials from boto3 session
        credentials = boto3_session.get_credentials()
        self.aws_access_key_id = credentials.access_key
        self.aws_secret_access_key = credentials.secret_key
        self.aws_session_token = credentials.token
        self.endpoint_url = endpoint_url

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize SQS client
        self.sqs_client = self._create_sqs_client(boto3_session.region_name)

    def _create_sqs_client(self, region_name: str):
        self.logger.info("Initializing SQS client with:")
        self.logger.info(f"  Region: {region_name}")
        self.logger.info(f"  Endpoint URL: {self.endpoint_url}")
        self.logger.info(f"  Access Key ID: {self.aws_access_key_id}")
        self.logger.info(
            f"  Secret Access Key: {'*' * len(self.aws_secret_access_key) if self.aws_secret_access_key else 'Not Set'}"
        )
        self.logger.info(
            f"  Session Token: {'Set' if self.aws_session_token else 'Not Set'}"
        )

        client_kwargs = {
            "region_name": region_name,
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
        }

        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        if self.aws_session_token:
            client_kwargs["aws_session_token"] = self.aws_session_token

        return boto3.client("sqs", **client_kwargs)

    async def start(self, process_message: Callable[[Dict[str, Any]], None]):
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
                        validate(instance=get_detail, schema=self.schema)

                        await asyncio.wait_for(
                            asyncio.to_thread(process_message, body),
                            timeout=self.processing_timeout,
                        )

                        self.sqs_client.delete_message(
                            QueueUrl=self.queue_url,
                            ReceiptHandle=message["ReceiptHandle"],
                        )
                        self.logger.info("Message processed and deleted from queue")
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
