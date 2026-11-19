import json
import os
import unittest.mock as mock

import boto3
import pytest
from moto import mock_aws

import check_new_packages
import check_python_versions
import get_pr_number
import invoke_pipelines
import load_config
import update_pr
from common.dynamodb import map_keys
from common.get_config import get_common_service_url, reset_url_cache


class DummyContext:
    function_name = "test-fn"
    memory_limit_in_mb = 256
    invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-fn"
    aws_request_id = "test-request-id"


@pytest.fixture
def lambda_context():
    return DummyContext()


@pytest.fixture(autouse=True)
def clean_env():
    """Ensure environment is clean between tests."""
    reset_url_cache()
    old_env = os.environ.copy()
    os.environ["STAGE"] = "Klayers-devp38"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ.pop("COMMON_SERVICE_URL", None)
    yield
    os.environ.clear()
    os.environ.update(old_env)
    reset_url_cache()


def test_get_config_from_env():
    os.environ["COMMON_SERVICE_URL"] = "https://custom-api.klayers.cloud/"
    url = get_common_service_url()
    assert url == "https://custom-api.klayers.cloud"


@mock_aws
def test_get_config_ssm_lookup_and_caching():
    ssm = boto3.client("ssm", region_name="us-east-1")
    param_name = "/common-service/Klayers-devp38/CommonServiceApi/URL"
    ssm.put_parameter(
        Name=param_name,
        Value="https://ssm-resolved.execute-api.us-east-1.amazonaws.com/dev/",
        Type="String",
    )

    url1 = get_common_service_url()
    assert url1 == "https://ssm-resolved.execute-api.us-east-1.amazonaws.com/dev"

    # Delete or change parameter in SSM to verify cache hit
    ssm.delete_parameter(Name=param_name)

    url2 = get_common_service_url()
    assert url2 == "https://ssm-resolved.execute-api.us-east-1.amazonaws.com/dev"


@mock_aws
def test_check_new_packages(lambda_context):
    # Setup mock S3
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-config-bucket"
    s3.create_bucket(Bucket=bucket)
    os.environ["CONFIG_BUCKET"] = bucket

    config_json = {"p3.13": {"packages_file": "packages_p313.csv"}}
    s3.put_object(Bucket=bucket, Key="config.json", Body=json.dumps(config_json))

    csv_content = "Package_Name\nrequests\npandas[extra]\nflask\n"
    s3.put_object(Bucket=bucket, Key="packages_p313.csv", Body=csv_content)

    # Mock common service response (dynamodb currently has requests and flask)
    with mock.patch("check_new_packages.get_from_common_service") as mock_cs:
        mock_cs.return_value = ["requests", "flask"]

        res = check_new_packages.main("p3.13", lambda_context)

        assert res["python_version"] == "p3.13"
        # pandas[extra] trimmed to pandas, which is not in dynamo
        assert res["new_packages"] == ["pandas"]


@mock_aws
def test_invoke_pipelines(lambda_context):
    boto3.client("events", region_name="us-east-1")

    event_payload = [
        {"python_version": "p3.13", "new_packages": ["pkg1", "pkg2"]},
        {"python_version": "p3.12", "new_packages": []},
    ]

    res = invoke_pipelines.main(event_payload, lambda_context)
    assert res == event_payload


def test_get_pr_number_no_commit(lambda_context):
    res = get_pr_number.main({}, lambda_context)
    assert res == {"pr_number": False}


def test_get_pr_number_with_pr(lambda_context):
    mock_response = mock.MagicMock()
    mock_response.content = b'[{"number": 123}]'
    mock_response.json.return_value = [{"number": 123}]

    with mock.patch("requests.get", return_value=mock_response):
        res = get_pr_number.main({"after": "c0ffee1234"}, lambda_context)
        assert res == {"pr_number": 123}


def test_get_pr_number_no_pr_found(lambda_context):
    mock_response = mock.MagicMock()
    mock_response.content = b"[]"
    mock_response.json.return_value = []

    with mock.patch("requests.get", return_value=mock_response):
        res = get_pr_number.main({"after": "c0ffee1234"}, lambda_context)
        assert res == {"pr_number": False}


def test_check_python_versions(lambda_context):
    with mock.patch("check_python_versions.get_from_common_service") as mock_cs:
        mock_cs.return_value = ["p3.12", "p3.13"]
        res = check_python_versions.main({}, lambda_context)
        assert res == ["p3.12", "p3.13"]


def test_load_config(lambda_context):
    with mock.patch("load_config.get_from_common_service") as mock_cs:
        mock_cs.return_value = {"status": "ok"}
        event = ({"python_version": "p3.13"}, {"pr_number": 42})
        res = load_config.main(event, lambda_context)
        assert res == event


def test_update_pr(lambda_context):
    res = update_pr.main({}, lambda_context)
    assert res is None


def test_map_keys():
    items = [
        {
            "pckg": "requests",
            "lyrVrsn": 1,
            "rqrmntsTxt": "urllib3\ncertifi",
            "exDt": 1700000000,
        }
    ]
    mapped = map_keys(items)
    assert mapped[0]["package"] == "requests"
    assert mapped[0]["layerVersion"] == 1
    assert mapped[0]["dependencies"] == ["urllib3", "certifi"]
    assert "2023-" in mapped[0]["expiryDate"]
