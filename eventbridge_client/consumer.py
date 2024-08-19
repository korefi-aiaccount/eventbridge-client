import asyncio
from typing import Callable, Dict, Any
import boto3
from botocore.exceptions import ClientError
from jsonschema import validate
from .schema_registry import SchemaRegistry
import logging
import os


class SQSConsumer:
    def __init__(
        self,
        queue_url: str,
        schema_registry: SchemaRegistry,
        schema_name: str,
        region_name: str,
        poll_interval: float = 1.0,
        visibility_timeout: int = 30,
        max_messages: int = 1,
        wait_time: int = 20,
        processing_timeout: float = 5.0,
    ):
        """
        Initialize the SQS Consumer.

        :param queue_url: The URL of the SQS queue to consume messages from.
        :param schema_registry: An instance of SchemaRegistry for schema validation.
        :param schema_name: The name of the schema to use for validation.
        :param region_name: The AWS region where the SQS queue is located.
        :param poll_interval: Time in seconds between each poll of the SQS queue. Default is 1 second.
        :param visibility_timeout: The visibility timeout for the queue in seconds. Default is 30 seconds.
        :param max_messages: The maximum number of messages to retrieve in a single poll. Default is 10.
        :param wait_time: The duration (in seconds) for which the call waits for a message to arrive
                          in the queue before returning. Default is 20 seconds (long polling).
        :param processing_timeout: Maximum time in seconds allowed for processing a single message.
                                   Default is 5 seconds.
        """
        self.queue_url = queue_url
        self.schema_registry = schema_registry
        self.schema_name = schema_name
        self.sqs_client = boto3.client("sqs", region_name=region_name)
        self.poll_interval = poll_interval
        self.visibility_timeout = visibility_timeout
        self.max_messages = max_messages
        self.wait_time = wait_time
        self.processing_timeout = processing_timeout
        self.is_running = False
        self.schema = self.schema_registry.get_schema(self.schema_name)

    async def start(self, process_message: Callable[[Dict[str, Any]], None]):
        """
        Start consuming messages from the SQS queue.

        :param process_message: A callable that processes a single message.
        """
        self.is_running = True

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        print("Getting AWS Creds")

        # Retrieve credentials from environment variables
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_session_token = os.getenv("AWS_SESSION_TOKEN")

        # Log the credentials if they are present
        if aws_access_key_id and aws_secret_access_key:
            print("Getting AWS Creds", aws_access_key_id)
            logger.info(f"AWS_ACCESS_KEY_ID: {aws_access_key_id}")
            logger.info(f"AWS_SECRET_ACCESS_KEY: {aws_secret_access_key}")
            if aws_session_token:
                logger.info(f"AWS_SESSION_TOKEN: {aws_session_token}")
        else:
            print("Getting AWS Creds, No")
            logger.warning("AWS credentials are not set in the environment variables.")

        while self.is_running:
            try:
                response = self.sqs_client.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=self.max_messages,
                    WaitTimeSeconds=self.wait_time,
                    VisibilityTimeout=self.visibility_timeout,
                )

                messages = response.get("Messages", [])
                for message in messages:
                    try:
                        body = message["Body"]
                        validate(instance=body, schema=self.schema)

                        # Process the message with a timeout
                        await asyncio.wait_for(
                            asyncio.to_thread(process_message, body),
                            timeout=self.processing_timeout,
                        )

                        # Delete the message from the queue
                        self.sqs_client.delete_message(
                            QueueUrl=self.queue_url,
                            ReceiptHandle=message["ReceiptHandle"],
                        )
                    except asyncio.TimeoutError:
                        print(
                            f"Message processing timed out after {self.processing_timeout} seconds"
                        )
                    except Exception as e:
                        print(f"Error processing message: {str(e)}")

            except ClientError as e:
                print(f"Error receiving messages: {str(e)}")

            await asyncio.sleep(self.poll_interval)

    def stop(self):
        """
        Stop consuming messages from the SQS queue.
        """
        self.is_running = False
