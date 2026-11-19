import os
import sys
import zipfile
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

import build


@pytest.fixture(autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def dynamodb_table():
    """Creates a mock DynamoDB table with pk (HASH) and sk (RANGE)."""
    with mock_aws():
        table_name = "test-klayers-db"
        os.environ["DB_NAME"] = table_name

        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName=table_name,
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
        yield table_name


@pytest.fixture
def s3_bucket():
    """Creates a mock S3 bucket."""
    with mock_aws():
        bucket_name = "test-klayers-bucket"
        os.environ["BUCKET_NAME"] = bucket_name

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=bucket_name)
        yield bucket_name


def test_check_python_version():
    current_major_minor = f"p{sys.version_info.major}.{sys.version_info.minor}"

    # Exact match
    assert build.check_python_version(current_major_minor) is True

    # Match with -arm64 suffix
    assert build.check_python_version(f"{current_major_minor}-arm64") is True

    # Mismatched version
    assert build.check_python_version("p2.7") is False
    assert build.check_python_version("p3.0") is False


def test_get_pk_sk_latest_build():
    pk, sk = build.get_pk_sk_latest_build(package="requests", python_version="p3.14")
    assert pk == {"S": "bldVrsn0#p3.14"}
    assert sk == {"S": "pckg#requests"}


def test_put_requirements_hash(dynamodb_table):
    client = boto3.client("dynamodb", region_name="us-east-1")

    # Initial put (version 1)
    build.put_requirements_hash(
        python_version="p3.14",
        package="requests",
        version="2.31.0",
        requirements_txt="requests==2.31.0\n",
        requirements_hash="hash123",
    )

    pk, sk = build.get_pk_sk_latest_build("requests", "p3.14")
    latest_item = client.get_item(TableName=dynamodb_table, Key={"pk": pk, "sk": sk})[
        "Item"
    ]
    assert latest_item["bltVrsn"]["N"] == "1"
    assert latest_item["rqrmntsHsh"]["S"] == "hash123"
    assert latest_item["pckgVrsn"]["S"] == "2.31.0"

    v1_item = client.get_item(
        TableName=dynamodb_table,
        Key={"pk": {"S": "bld#v1:p3.14"}, "sk": sk},
    )["Item"]
    assert v1_item["bltVrsn"]["N"] == "1"
    assert v1_item["pckg"]["S"] == "requests"
    assert v1_item["pyVrsn"]["S"] == "p3.14"

    # Second put (version 2)
    build.put_requirements_hash(
        python_version="p3.14",
        package="requests",
        version="2.32.0",
        requirements_txt="requests==2.32.0\n",
        requirements_hash="hash456",
    )

    latest_item_v2 = client.get_item(
        TableName=dynamodb_table, Key={"pk": pk, "sk": sk}
    )["Item"]
    assert latest_item_v2["bltVrsn"]["N"] == "2"
    assert latest_item_v2["rqrmntsHsh"]["S"] == "hash456"

    v2_item = client.get_item(
        TableName=dynamodb_table,
        Key={"pk": {"S": "bld#v2:p3.14"}, "sk": sk},
    )["Item"]
    assert v2_item["bltVrsn"]["N"] == "2"
    assert v2_item["pckgVrsn"]["S"] == "2.32.0"


def test_check_requirement_hash(dynamodb_table):
    # Put an initial record
    build.put_requirements_hash(
        python_version="p3.14",
        package="requests",
        version="2.31.0",
        requirements_txt="requests==2.31.0\n",
        requirements_hash="matching_hash_123",
    )

    # Hash matches
    assert (
        build.check_requirement_hash(
            package="requests",
            python_version="p3.14",
            requirements_hash="matching_hash_123",
        )
        is True
    )

    # Hash does not match
    assert (
        build.check_requirement_hash(
            package="requests",
            python_version="p3.14",
            requirements_hash="different_hash",
        )
        is False
    )

    # Package does not exist
    assert (
        build.check_requirement_hash(
            package="nonexistent_pkg",
            python_version="p3.14",
            requirements_hash="matching_hash_123",
        )
        is False
    )


def test_upload_to_s3(s3_bucket, tmp_path):
    dummy_file = tmp_path / "dummy.zip"
    dummy_file.write_bytes(b"PK\x03\x04test_content")

    uploaded_name = "p3.14/test_package.zip"
    result = build.upload_to_s3(
        zip_file=str(dummy_file),
        package="test_package",
        uploaded_file_name=uploaded_name,
    )

    assert result == uploaded_name

    s3 = boto3.client("s3", region_name="us-east-1")
    obj = s3.get_object(Bucket=s3_bucket, Key=uploaded_name)
    assert obj["Body"].read() == b"PK\x03\x04test_content"


def test_zip_dir(tmp_path):
    package_dir = Path("/tmp/test_pkg_dir")
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "sample.txt").write_text("hello world")

    zip_path = build.zip_dir(dir_path=str(package_dir), package="test_pkg_zip")
    assert os.path.exists(zip_path)
    assert zip_path == "/tmp/test_pkg_zip.zip"

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "test_pkg_dir/sample.txt" in namelist

    # Clean up
    if os.path.exists(zip_path):
        os.remove(zip_path)
    if package_dir.exists():
        for p in package_dir.glob("*"):
            p.unlink()
        package_dir.rmdir()
