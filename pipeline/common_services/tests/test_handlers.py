import json
import os

import boto3
import pytest
from moto import mock_aws


class DummyContext:
    function_name = "test-fn"
    memory_limit_in_mb = 256
    invoked_function_arn = "arn:aws:lambda:us-east-2:123456789012:function:test-fn"
    aws_request_id = "test-request-id"


@pytest.fixture(autouse=True)
def setup_env():
    os.environ["AWS_DEFAULT_REGION"] = "us-east-2"
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["STAGE"] = "Klayers-prodp38"
    os.environ["DB_NAME"] = "test-klayers-db"
    os.environ["CONFIG_BUCKET"] = "test-klayers-config"
    os.environ["POWERTOOLS_SERVICE_NAME"] = "Klayers.common-service"


@mock_aws
def test_end_to_end_handlers():
    # Clear any lru_cache
    from common.get_config import get_config_items

    get_config_items.cache_clear()

    import get_config
    import get_config_s3
    import get_python_versions
    import load_config_from_s3

    context = DummyContext()

    # Setup DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
    table = dynamodb.create_table(
        TableName="test-klayers-db",
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()

    # 1. Before loading config: verify get_python_versions returns 500
    resp_empty = get_python_versions.main({}, context)
    assert resp_empty["statusCode"] == 500
    body_empty = json.loads(resp_empty["body"])
    assert "No items in DB" in body_empty["message"]

    # Setup S3 with config files
    s3 = boto3.client("s3", region_name="us-east-2")
    s3.create_bucket(
        Bucket="test-klayers-config",
        CreateBucketConfiguration={"LocationConstraint": "us-east-2"},
    )

    config_data = {
        "python_versions": ["p3.13", "p3.13-arm64"],
        "p3.13": {"packages_file": "packages_p3.13.csv"},
        "p3.13-arm64": {"packages_file": "packages_p3.13-arm64.csv"},
    }
    s3.put_object(
        Bucket="test-klayers-config",
        Key="config.json",
        Body=json.dumps(config_data).encode("utf-8"),
    )

    packages_p313_csv = "Package_Name,Version\nrequests,2.31.0\nurllib3,2.0.7\n"
    s3.put_object(
        Bucket="test-klayers-config",
        Key="packages_p3.13.csv",
        Body=packages_p313_csv.encode("utf-8"),
    )

    packages_p313_arm_csv = "Package_Name,Version\nnumpy,1.26.0\n"
    s3.put_object(
        Bucket="test-klayers-config",
        Key="packages_p3.13-arm64.csv",
        Body=packages_p313_arm_csv.encode("utf-8"),
    )

    regions_csv = "Region_Name,Code\nUS East (Ohio),us-east-2\nUS East (N. Virginia),us-east-1\n"
    s3.put_object(
        Bucket="test-klayers-config",
        Key="regions.csv",
        Body=regions_csv.encode("utf-8"),
    )

    # 2. Test load_config_from_s3
    load_resp = load_config_from_s3.main({}, context)
    assert load_resp["statusCode"] == 200
    assert json.loads(load_resp["body"]) == {"message": "Loaded Config"}

    # Verify DynamoDB contents
    py_item = table.get_item(Key={"pk": "cnfg#pyVrsns", "sk": "all"})["Item"]
    assert py_item["cnfg"] == ["p3.13", "p3.13-arm64"]

    pkg_item = table.get_item(Key={"pk": "cnfg#pckgs", "sk": "p3.13"})["Item"]
    assert pkg_item["cnfg"] == ["requests", "urllib3"]

    rgn_item = table.get_item(Key={"pk": "cnfg#rgns", "sk": "p3.13"})["Item"]
    assert rgn_item["cnfg"] == ["us-east-2", "us-east-1"]

    # 3. Test get_python_versions after config load
    get_config_items.cache_clear()
    py_vrsns_resp = get_python_versions.main({}, context)
    assert py_vrsns_resp["statusCode"] == 200
    assert json.loads(py_vrsns_resp["body"]) == ["p3.13", "p3.13-arm64"]

    # 4. Test get_config for packages and regions
    get_config_items.cache_clear()
    pkg_resp = get_config.main(
        {"pathParameters": {"python_version": "p3.13", "config_type": "pckgs"}},
        context,
    )
    assert pkg_resp["statusCode"] == 200
    assert json.loads(pkg_resp["body"]) == ["requests", "urllib3"]

    rgn_resp = get_config.main(
        {"pathParameters": {"python_version": "p3.13", "config_type": "rgns"}},
        context,
    )
    assert rgn_resp["statusCode"] == 200
    assert json.loads(rgn_resp["body"]) == ["us-east-2", "us-east-1"]

    # 5. Test get_config_s3 for packages and regions
    s3_pkg_resp = get_config_s3.main(
        {"pathParameters": {"python_version": "p3.13", "config_type": "pckgs"}},
        context,
    )
    assert s3_pkg_resp["statusCode"] == 200
    assert json.loads(s3_pkg_resp["body"]) == ["requests", "urllib3"]

    s3_rgn_resp = get_config_s3.main(
        {"pathParameters": {"python_version": "p3.13", "config_type": "rgns"}},
        context,
    )
    assert s3_rgn_resp["statusCode"] == 200
    assert json.loads(s3_rgn_resp["body"]) == ["us-east-2", "us-east-1"]

    # 6. Test get_config_s3 with unknown config_type
    s3_unknown_resp = get_config_s3.main(
        {"pathParameters": {"python_version": "p3.13", "config_type": "unknown"}},
        context,
    )
    assert s3_unknown_resp["statusCode"] == 200
    assert json.loads(s3_unknown_resp["body"]) == []
