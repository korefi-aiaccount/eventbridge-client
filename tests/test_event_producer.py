# import pytest
# from unittest.mock import Mock, patch
# from botocore.exceptions import ClientError
# from jsonschema import ValidationError
# from eventbridge_client import EventProducer, SchemaRegistry


# @pytest.fixture
# def mock_eventbridge():
#     return Mock()


# @pytest.fixture
# def mock_schema_registry():
#     return Mock()


# @pytest.fixture
# def event_producer(mock_eventbridge, mock_schema_registry):
#     producer = EventProducer("apicurio", "http://test-url")
#     producer.eventbridge = mock_eventbridge
#     producer.schema_registry = mock_schema_registry
#     return producer


# def test_produce_success(event_producer, mock_eventbridge, mock_schema_registry):
#     # Arrange
#     event_bus_name = "test-bus"
#     event_source = "test-source"
#     detail_type = "test-type"
#     detail = {"key": "value"}
#     schema_name = "test-schema"
#     expected_response = {"Entries": [{"EventId": "1234"}]}

#     mock_schema_registry.get_schema.return_value = {"type": "object"}
#     mock_eventbridge.put_events.return_value = expected_response

#     # Act
#     response = event_producer.produce(
#         event_bus_name, event_source, detail_type, detail, schema_name
#     )

#     # Assert
#     assert response == expected_response
#     mock_schema_registry.get_schema.assert_called_once_with(schema_name)
#     mock_eventbridge.put_events.assert_called_once()


# def test_produce_validation_error(event_producer, mock_schema_registry):
#     # Arrange
#     event_bus_name = "test-bus"
#     event_source = "test-source"
#     detail_type = "test-type"
#     detail = {"key": "value"}
#     schema_name = "test-schema"

#     mock_schema_registry.get_schema.return_value = {
#         "type": "object",
#         "required": ["missing_key"],
#     }

#     # Act & Assert
#     with pytest.raises(ValidationError):
#         event_producer.produce(
#             event_bus_name, event_source, detail_type, detail, schema_name
#         )


# def test_produce_client_error(event_producer, mock_eventbridge, mock_schema_registry):
#     # Arrange
#     event_bus_name = "test-bus"
#     event_source = "test-source"
#     detail_type = "test-type"
#     detail = {"key": "value"}
#     schema_name = "test-schema"

#     mock_schema_registry.get_schema.return_value = {"type": "object"}
#     mock_eventbridge.put_events.side_effect = ClientError(
#         {"Error": {"Code": "TestException", "Message": "Test error"}}, "PutEvents"
#     )

#     # Act & Assert
#     with pytest.raises(ClientError):
#         event_producer.produce(
#             event_bus_name, event_source, detail_type, detail, schema_name
#         )


# @pytest.fixture
# def mock_boto3_client():
#     with patch("eventbridge_client.schema_registry.boto3.client") as mock_client:
#         yield mock_client


# @pytest.fixture
# def mock_requests_get():
#     with patch("eventbridge_client.schema_registry.requests.get") as mock_get:
#         yield mock_get


# @pytest.mark.parametrize(
#     "registry_type, schema_id, expected_schema, mock_response",
#     [
#         (
#             "eventbridge",
#             "test-schema",
#             {"type": "object"},
#             {"Content": '{"type": "object"}'},
#         ),
#         (
#             "apicurio",
#             "test-schema",
#             {"type": "object"},
#             {"components": {"schemas": {"TestSchema": {"type": "object"}}}},
#         ),
#     ],
# )
# def test_get_schema(
#     registry_type,
#     schema_id,
#     expected_schema,
#     mock_response,
#     mock_boto3_client,
#     mock_requests_get,
# ):
#     # Arrange
#     if registry_type == "eventbridge":
#         mock_schemas = Mock()
#         mock_boto3_client.return_value = mock_schemas
#         mock_schemas.describe_schema.return_value = mock_response
#         schema_registry = SchemaRegistry(registry_type, region_name="us-west-2")
#     else:  # apicurio
#         mock_response_obj = Mock()
#         mock_response_obj.json.return_value = mock_response
#         mock_requests_get.return_value = mock_response_obj
#         schema_registry = SchemaRegistry(registry_type, url="http://test-url")

#     # Act
#     result = schema_registry.get_schema(schema_id)

#     # Assert
#     assert result == expected_schema
#     if registry_type == "eventbridge":
#         mock_schemas.describe_schema.assert_called_once_with(SchemaName=schema_id)
#     else:  # apicurio
#         mock_requests_get.assert_called_once_with(
#             f"http://test-url/apis/registry/v2/groups/default/artifacts/{schema_id}",
#             timeout=5,
#         )


# def test_unsupported_registry_type():
#     # Arrange
#     schema_registry = SchemaRegistry("unsupported")

#     # Act & Assert
#     with pytest.raises(ValueError, match="Unsupported registry type: unsupported"):
#         schema_registry.get_schema("test-schema")


# @pytest.mark.parametrize(
#     "registry_type, exception_class, exception_message",
#     [
#         ("eventbridge", ClientError, "Error fetching schema from EventBridge"),
#         ("apicurio", Exception, "Failed to retrieve schema from Apicurio"),
#     ],
# )
# def test_get_schema_error_handling(
#     registry_type,
#     exception_class,
#     exception_message,
#     mock_boto3_client,
#     mock_requests_get,
# ):
#     # Arrange
#     if registry_type == "eventbridge":
#         mock_schemas = Mock()
#         mock_boto3_client.return_value = mock_schemas
#         mock_schemas.describe_schema.side_effect = ClientError(
#             {"Error": {"Code": "TestException", "Message": "Test error"}},
#             "DescribeSchema",
#         )
#         schema_registry = SchemaRegistry(registry_type, region_name="us-west-2")
#     else:  # apicurio
#         mock_requests_get.side_effect = Exception("Test error")
#         schema_registry = SchemaRegistry(registry_type, url="http://test-url")

#     # Act & Assert
#     with pytest.raises(exception_class), pytest.warns(
#         UserWarning, match=exception_message
#     ):
#         schema_registry.get_schema("test-schema")
