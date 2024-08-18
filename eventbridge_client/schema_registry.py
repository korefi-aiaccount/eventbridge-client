import json
import warnings
import boto3
import requests
from botocore.exceptions import ClientError
from functools import lru_cache


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
            warnings.warn(f"Error fetching schema from EventBridge: {e}")
            raise

    def _get_apicurio_schema(self, schema_id):
        url = f"{self.url}/apis/registry/v2/groups/default/artifacts/{schema_id}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            response_data = response.json()
            schema_name = next(iter(response_data["components"]["schemas"]))
            actual_schema = response_data["components"]["schemas"][schema_name]
            return actual_schema
        except Exception as e:
            warnings.warn(f"Failed to retrieve schema from Apicurio: {e}")
            raise
