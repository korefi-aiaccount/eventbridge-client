import pytest
from unittest.mock import MagicMock, patch
import asyncio
import boto3

# from botocore.exceptions import ClientError
from eventbridge_client import SQSConsumer, SchemaRegistry


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_boto3_session():
    session = MagicMock(spec=boto3.Session)
    credentials = MagicMock()
    credentials.access_key = "test_access_key"
    credentials.secret_key = "test_secret_key"
    credentials.token = "test_token"
    session.get_credentials.return_value = credentials
    return session


@pytest.fixture
def mock_schema_registry():
    registry = MagicMock(spec=SchemaRegistry)
    registry.get_schema.return_value = {"type": "object"}
    return registry


@pytest.fixture
def mock_sqs_client():
    return MagicMock()


@pytest.fixture
def sqs_consumer(mock_boto3_session, mock_schema_registry, mock_sqs_client):
    with patch("boto3.client", return_value=mock_sqs_client):
        consumer = SQSConsumer(
            queue_url="http://test-queue-url",
            schema_registry=mock_schema_registry,
            schema_name="test-schema",
            boto3_session=mock_boto3_session,
            endpoint_url="http://test-endpoint-url",
        )
    return consumer


# @pytest.mark.asyncio
# async def test_start_and_process_message(sqs_consumer, mock_sqs_client):
#     mock_sqs_client.receive_message.return_value = {
#         "Messages": [
#             {
#                 "Body": '{"detail": {"test": "data"}}',
#                 "ReceiptHandle": "test-receipt-handle",
#             }
#         ]
#     }

#     mock_process_message = MagicMock()

#     async def run_consumer():
#         await sqs_consumer.start(mock_process_message)

#     async def stop_after_delay():
#         await asyncio.sleep(0.5)
#         sqs_consumer.stop()

#     await asyncio.gather(run_consumer(), stop_after_delay())

#     mock_sqs_client.receive_message.assert_called()
#     mock_process_message.assert_called_once()
#     mock_sqs_client.delete_message.assert_called_once()


# @pytest.mark.asyncio
# async def test_message_processing_timeout(sqs_consumer, mock_sqs_client):
#     mock_sqs_client.receive_message.return_value = {
#         "Messages": [
#             {
#                 "Body": '{"detail": {"test": "data"}}',
#                 "ReceiptHandle": "test-receipt-handle",
#             }
#         ]
#     }

#     async def slow_process_message(_):
#         await asyncio.sleep(0.2)  # Longer than the processing_timeout

#     sqs_consumer.processing_timeout = 0.1  # Set a short timeout for testing

#     async def run_consumer():
#         await sqs_consumer.start(slow_process_message)

#     async def stop_after_delay():
#         await asyncio.sleep(0.3)
#         sqs_consumer.stop()

#     with pytest.raises(asyncio.TimeoutError):
#         await asyncio.gather(run_consumer(), stop_after_delay())


# @pytest.mark.parametrize(
#     "error_type,expected_log",
#     [
#         (
#             ClientError(
#                 {
#                     "Error": {
#                         "Code": "InvalidClientTokenId",
#                         "Message": "The security token included in the request is invalid",
#                     }
#                 },
#                 "operation",
#             ),
#             "Invalid AWS credentials",
#         ),
#         (Exception("Generic error"), "Error processing message"),
#     ],
# )
# @pytest.mark.asyncio
# async def test_error_handling(
#     error_type, expected_log, sqs_consumer, mock_sqs_client, caplog
# ):
#     mock_sqs_client.receive_message.side_effect = error_type

#     async def run_consumer():
#         await sqs_consumer.start(MagicMock())

#     async def stop_after_delay():
#         await asyncio.sleep(0.1)
#         sqs_consumer.stop()

#     await asyncio.gather(run_consumer(), stop_after_delay())

#     assert expected_log in caplog.text
