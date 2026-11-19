import importlib
import json
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws
from packaging.version import parse

from common import get_config

check = importlib.import_module("02_pipeline.check")
stream_processor = importlib.import_module("04_stream_processor.stream_processor")
layer_delete = importlib.import_module("04_stream_processor.layer_delete")


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-2")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-2")
    monkeypatch.setenv("STAGE", "Klayers-defaultp38")
    monkeypatch.setenv("DB_NAME", "kl.Klayers-defaultp38.db-ver2")
    monkeypatch.setenv("STREAM_LABEL", "test-stream-label")


@pytest.fixture
def dummy_context():
    context = MagicMock()
    context.function_name = "test_func"
    context.memory_limit_in_mb = 256
    context.invoked_function_arn = "arn:aws:lambda:us-east-2:123456789012:function:test"
    context.aws_request_id = "test-request-id"
    return context


# ---------------------------------------------------------------------------
# Dynamic get_config tests
# ---------------------------------------------------------------------------
def test_get_config_env_url(monkeypatch):
    monkeypatch.setenv("COMMON_SERVICE_URL", "https://api.test.klayers.cloud/")
    url = get_config.get_common_service_url()
    assert url == "https://api.test.klayers.cloud"


@mock_aws
def test_get_config_ssm_lookup(monkeypatch):
    monkeypatch.delenv("COMMON_SERVICE_URL", raising=False)
    # reset cache
    get_config._cached_url = None
    get_config._cached_time = 0.0

    ssm = boto3.client("ssm", region_name="us-east-2")
    ssm.put_parameter(
        Name="/common-service/Klayers-defaultp38/CommonServiceApi/URL",
        Value="https://ssm.test.klayers.cloud/v1/",
        Type="String",
    )

    url = get_config.get_common_service_url()
    assert url == "https://ssm.test.klayers.cloud/v1"

    # Verify cache works within 300s
    ssm.put_parameter(
        Name="/common-service/Klayers-defaultp38/CommonServiceApi/URL",
        Value="https://updated.test.klayers.cloud/",
        Type="String",
        Overwrite=True,
    )
    # Still returns cached url
    assert get_config.get_common_service_url() == "https://ssm.test.klayers.cloud/v1"


# ---------------------------------------------------------------------------
# Check tests
# ---------------------------------------------------------------------------
def test_check_get_latest_release():
    mock_pypi_response = MagicMock()
    mock_pypi_response.status_code = 200
    mock_pypi_response.text = json.dumps(
        {
            "releases": {
                "1.0.0": [],
                "2.0.0a1": [],
                "1.9.0": [],
            },
            "info": {"license": "MIT"},
        }
    )

    with patch("requests.get", return_value=mock_pypi_response):
        ver, license_info = check.get_latest_release("testpkg")
        assert ver == parse("1.9.0")
        assert license_info == "MIT"


# ---------------------------------------------------------------------------
# Stream processor tests
# ---------------------------------------------------------------------------
@mock_aws
def test_stream_processor(dummy_context):
    events_client = boto3.client("events", region_name="us-east-2")
    mock_event = {
        "Records": [
            {
                "eventName": "REMOVE",
                "dynamodb": {
                    "Keys": {
                        "pk": {"S": "lyr#requests"},
                        "sk": {"S": "vrsn#1"},
                    }
                },
            }
        ]
    }

    with patch.object(events_client, "put_events", return_value={"FailedEntryCount": 0}):
        stream_processor.main(mock_event, dummy_context)


# ---------------------------------------------------------------------------
# Layer delete tests
# ---------------------------------------------------------------------------
@mock_aws
def test_layer_delete(dummy_context):
    dynamodb = boto3.client("dynamodb", region_name="us-east-2")
    dynamodb.create_table(
        TableName="kl.Klayers-defaultp38.db-ver2",
        KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    mock_event = {
        "detail": {
            "record": {
                "dynamodb": {
                    "OldImage": {
                        "pk": {"S": "lyr#requests"},
                        "arn": {"S": "arn:aws:lambda:us-east-2:123456789012:layer:Klayers-p312-requests:1"},
                        "dplySts": {"S": "expired"},
                        "exDt": {"N": "1700000000"},
                    }
                }
            }
        }
    }

    with patch("boto3.client") as mock_boto:
        mock_lambda = MagicMock()
        mock_boto.side_effect = lambda service, **kwargs: mock_lambda if service == "lambda" else dynamodb

        layer_delete.main(mock_event, dummy_context)
        mock_lambda.delete_layer_version.assert_called_once_with(LayerName="Klayers-p312-requests", VersionNumber=1)
