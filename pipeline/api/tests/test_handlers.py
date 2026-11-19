import csv
import io
import json
from dataclasses import dataclass

import boto3
import pytest
from moto import mock_aws

from builds.list_builds import main as list_builds_main
from layers.latest_region import main as latest_region_main
from layers.latest_region_package import main as latest_region_package_main
from layers.list_layer_version import main as list_layer_version_main

TABLE_NAME = "kl.Klayers-defaultp38.db-ver2"


@dataclass
class LambdaContext:
    function_name: str = "test-fn"
    memory_limit_in_mb: int = 256
    invoked_function_arn: str = (
        "arn:aws:lambda:ap-southeast-1:123456789012:function:test-fn"
    )
    aws_request_id: str = "test-request-id"


@pytest.fixture
def context():
    return LambdaContext()


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    monkeypatch.setenv("AWS_REGION", "ap-southeast-1")
    monkeypatch.setenv("DB_NAME", TABLE_NAME)
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", "Klayers.api")


@pytest.fixture
def dynamodb_table():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
                {"AttributeName": "rgn#PyVrsn", "AttributeType": "S"},
                {"AttributeName": "dplySts", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "deployed_in_region_by_python_version",
                    "KeySchema": [
                        {"AttributeName": "rgn#PyVrsn", "KeyType": "HASH"},
                        {"AttributeName": "dplySts", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield table


def test_latest_region_package_found(dynamodb_table, context):
    dynamodb_table.put_item(
        Item={
            "pk": "lyr#us-east-1:requests:p3.13",
            "sk": "lyrVrsn0#",
            "rgn": "us-east-1",
            "pckg": "requests",
            "arn": "arn:aws:lambda:us-east-1:123456789012:layer:Klayers-p313-requests:1",
            "pckgVrsn": "2.31.0",
            "rqrmntsTxt": "requests==2.31.0\nurllib3==2.0.0",
        }
    )

    event = {
        "pathParameters": {
            "region": "us-east-1",
            "package": "requests",
            "python_version": "p3.13",
        }
    }
    resp = latest_region_package_main(event, context)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "application/json"
    body = json.loads(resp["body"])
    assert body["package"] == "requests"
    assert body["region"] == "us-east-1"
    assert (
        body["arn"]
        == "arn:aws:lambda:us-east-1:123456789012:layer:Klayers-p313-requests:1"
    )
    assert body["packageVersion"] == "2.31.0"
    assert body["dependencies"] == ["requests==2.31.0", "urllib3==2.0.0"]


def test_latest_region_package_not_found(dynamodb_table, context):
    event = {
        "pathParameters": {
            "region": "us-east-1",
            "package": "nonexistent",
            "python_version": "p3.13",
        }
    }
    resp = latest_region_package_main(event, context)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "application/json"
    assert json.loads(resp["body"]) == {}


def test_latest_region_package_none_path_parameters(dynamodb_table, context):
    event = {"pathParameters": None}
    resp = latest_region_package_main(event, context)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"]) == {}


def test_latest_region_json(dynamodb_table, context):
    dynamodb_table.put_item(
        Item={
            "pk": "item1",
            "sk": "item1",
            "rgn#PyVrsn": "us-east-1:p3.13",
            "dplySts": "latest",
            "pckg": "requests",
            "pckgVrsn": "2.31.0",
            "arn": "arn:aws:lambda:us-east-1:123456789012:layer:Klayers-p313-requests:1",
        }
    )

    event = {
        "pathParameters": {
            "region": "us-east-1",
            "python_version": "p3.13",
            "format": "json",
        }
    }
    resp = latest_region_main(event, context)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "application/json"
    body = json.loads(resp["body"])
    assert len(body) == 1
    assert body[0]["package"] == "requests"
    assert body[0]["packageVersion"] == "2.31.0"
    assert (
        body[0]["arn"]
        == "arn:aws:lambda:us-east-1:123456789012:layer:Klayers-p313-requests:1"
    )


def test_latest_region_csv(dynamodb_table, context):
    dynamodb_table.put_item(
        Item={
            "pk": "item1",
            "sk": "item1",
            "rgn#PyVrsn": "us-east-1:p3.13",
            "dplySts": "latest",
            "pckg": "requests",
            "pckgVrsn": "2.31.0",
            "arn": "arn:aws:lambda:us-east-1:123456789012:layer:Klayers-p313-requests:1",
        }
    )

    event = {
        "pathParameters": {
            "region": "us-east-1",
            "python_version": "p3.13",
            "format": "csv",
        }
    }
    resp = latest_region_main(event, context)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "text/html"
    assert (
        resp["headers"]["Content-Disposition"]
        == 'attachment; filename="klayers-us-east-1-p3.13.csv"'
    )

    reader = csv.reader(io.StringIO(resp["body"]))
    rows = list(reader)
    assert rows[0] == ["Package", "Package Version", "arn"]
    assert rows[1] == [
        "requests",
        "2.31.0",
        "arn:aws:lambda:us-east-1:123456789012:layer:Klayers-p313-requests:1",
    ]


def test_latest_region_html(dynamodb_table, context):
    dynamodb_table.put_item(
        Item={
            "pk": "item1",
            "sk": "item1",
            "rgn#PyVrsn": "us-east-1:p3.13",
            "dplySts": "latest",
            "pckg": "requests",
            "pckgVrsn": "2.31.0",
            "arn": "arn:aws:lambda:us-east-1:123456789012:layer:Klayers-p313-requests:1",
        }
    )

    event = {
        "pathParameters": {
            "region": "us-east-1",
            "python_version": "p3.13",
            "format": "html",
        }
    }
    resp = latest_region_main(event, context)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "text/html"
    assert "<table>" in resp["body"]
    assert "Package Version" in resp["body"]
    assert "requests" in resp["body"]


def test_latest_region_none_path_parameters(dynamodb_table, context):
    event = {"pathParameters": None}
    resp = latest_region_main(event, context)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "application/json"
    assert json.loads(resp["body"]) == []


def test_list_layer_version(dynamodb_table, context):
    pk = "lyr#us-east-1:requests:p3.13"
    dynamodb_table.put_item(
        Item={
            "pk": pk,
            "sk": "lyrVrsn1#",
            "dplySts": "deployed",
            "arn": "arn:aws:lambda:us-east-1:123456789012:layer:Klayers-p313-requests:1",
            "pckgVrsn": "2.31.0",
            "rqrmntsTxt": "requests==2.31.0",
            "exDt": 1700000000,
        }
    )
    # Item without dplySts should be filtered out
    dynamodb_table.put_item(
        Item={
            "pk": pk,
            "sk": "lyrVrsn0#",
            "arn": "arn:aws:lambda:us-east-1:123456789012:layer:Klayers-p313-requests:1",
            "pckgVrsn": "2.31.0",
        }
    )

    event = {
        "pathParameters": {
            "region": "us-east-1",
            "package": "requests",
            "python_version": "p3.13",
        }
    }
    resp = list_layer_version_main(event, context)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "application/json"
    body = json.loads(resp["body"])
    assert len(body) == 1
    assert (
        body[0]["arn"]
        == "arn:aws:lambda:us-east-1:123456789012:layer:Klayers-p313-requests:1"
    )
    assert body[0]["deployStatus"] == "deployed"
    assert body[0]["packageVersion"] == "2.31.0"
    assert body[0]["dependencies"] == ["requests==2.31.0"]
    assert "expiryDate" in body[0]


def test_list_builds(dynamodb_table, context):
    dynamodb_table.put_item(
        Item={
            "pk": "bldVrsn0#p3.13",
            "sk": "requests",
            "crtdDt": "2026-11-14T12:00:00.000Z",
            "pckg": "requests",
            "pckgVrsn": "2.31.0",
            "rqrmntsTxt": "requests==2.31.0\nurllib3==2.0.0",
        }
    )

    event = {
        "pathParameters": {
            "python_version": "p3.13",
        }
    }
    resp = list_builds_main(event, context)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "application/json"
    body = json.loads(resp["body"])
    assert len(body) == 1
    assert body[0]["package"] == "requests"
    assert body[0]["packageVersion"] == "2.31.0"
    assert body[0]["createdDateTime"] == "2026-11-14T12:00:00"
    assert body[0]["dependencies"] == ["requests==2.31.0", "urllib3==2.0.0"]
