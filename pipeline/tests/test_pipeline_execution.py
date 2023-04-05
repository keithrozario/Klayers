import boto3
import json
import time
import get_config
from datetime import datetime

from botocore.exceptions import ClientError

stage = "Klayers-defaultp38"
config, session = get_config.get_config(stage)
table_name = f"{config['app_name']}.{stage}.db"
package = "boto3"
region = config["aws_region"]


def run_pipeline_till_success(package="boto3"):
    client = session.client("stepfunctions")
    response = client.start_execution(
        stateMachineArn=config["step_functions_arn"]["pipeline"],
        name=f"{datetime.now().isoformat().replace('-','_').replace(':','_')}_test_{package}",
        input=json.dumps({"detail": {"package": package}}),
    )

    execution_arn = response["executionArn"]
    assert execution_arn

    response = {"status": "RUNNING"}
    while response["status"] == "RUNNING":
        response = client.describe_execution(executionArn=execution_arn)
        time.sleep(0.5)
    assert response["status"] == "SUCCEEDED"
    output = json.loads(response["output"])

    return output


def get_latest_build(package="boto3"):
    client = session.client("dynamodb")

    pk_latest = "bldVrsn0#"
    sk = f"pckg#{package}"

    response = client.get_item(
        TableName=table_name,
        Key={
            "pk": {"S": pk_latest},
            "sk": {"S": sk},
        },
    )
    pk_bld = response["Item"]["bltVrsn"]["S"]

    return pk_bld


def update_build(package="boto3"):
    dynamo_client = session.client("dynamodb")

    pk_latest = "bldVrsn0#"
    sk = f"pckg#{package}"
    pk_bld = get_latest_build(package=package)

    # Update rqrmntsHsh to "dummy", forcing a new build
    response = dynamo_client.transact_write_items(
        TransactItems=[
            {
                "Update": {
                    "TableName": table_name,
                    "Key": {
                        "pk": {"S": pk_latest},
                        "sk": {"S": sk},
                    },
                    "UpdateExpression": "set rqrmntsHsh = :rqrmntsHsh",
                    "ExpressionAttributeValues": {
                        ":rqrmntsHsh": {"S": "dummy"},
                    },
                }
            },
            {
                "Update": {
                    "TableName": table_name,
                    "Key": {
                        "pk": {"S": pk_bld},
                        "sk": {"S": sk},
                    },
                    "UpdateExpression": "set rqrmntsHsh = :rqrmntsHsh",
                    "ExpressionAttributeValues": {
                        ":rqrmntsHsh": {"S": "dummy"},
                    },
                }
            },
        ]
    )

    return pk_bld


def get_latest_layer_version(package="boto3", region="ap-southeast-1"):
    """
    return:
        layer_version (int): returns latest layer version as an integer!
    """
    client = session.client("dynamodb")

    pk = f"lyr#{region}.{package}"
    sk = "lyrVrsn0#"

    response = client.get_item(
        TableName=table_name,
        Key={
            "pk": {"S": pk},
            "sk": {"S": sk},
        },
    )
    layer_version = response["Item"]["lyrVrsn"]["N"]

    return int(layer_version)


def get_layer_record(layer_version, package="boto3", region="ap-southeast-1"):
    client = session.client("dynamodb")

    pk = f"lyr#{region}.{package}"
    sk = f"lyrVrsn#v{layer_version}"

    response = client.get_item(
        TableName=table_name,
        Key={
            "pk": {"S": pk},
            "sk": {"S": sk},
        },
    )

    return response["Item"]


def update_layer(package="boto3", region="ap-southeast-1"):
    dynamo_client = session.client("dynamodb")
    latest_layer_version = get_latest_layer_version(package, region)

    pk = f"lyr#{region}.{package}"
    sk = "lyrVrsn0#"
    sk_latest = f"lyrVrsn#v{latest_layer_version}"

    # Update rqrmntsHsh to "dummy", forcing a new build
    response = dynamo_client.transact_write_items(
        TransactItems=[
            {
                "Update": {
                    "TableName": table_name,
                    "Key": {
                        "pk": {"S": pk},
                        "sk": {"S": sk},
                    },
                    "UpdateExpression": "set rqrmntsHsh = :rqrmntsHsh",
                    "ExpressionAttributeValues": {
                        ":rqrmntsHsh": {"S": "dummy"},
                    },
                }
            },
            {
                "Update": {
                    "TableName": table_name,
                    "Key": {
                        "pk": {"S": pk},
                        "sk": {"S": sk_latest},
                    },
                    "UpdateExpression": "set rqrmntsHsh = :rqrmntsHsh",
                    "ExpressionAttributeValues": {
                        ":rqrmntsHsh": {"S": "dummy"},
                    },
                }
            },
        ]
    )

    return latest_layer_version


def check_layer(arn):
    client = session.client("lambda")
    try:
        response = client.get_layer_version_by_arn(Arn=arn)
    except ClientError:
        return None

    return response


def delete_layer(layer_version, package="boto3", region="ap-southeast-1"):
    client = session.client("dynamodb")

    pk = f"lyr#{region}.{package}"
    sk = f"lyrVrsn#v{layer_version}"

    response = client.delete_item(
        TableName=table_name,
        Key={
            "pk": {"S": pk},
            "sk": {"S": sk},
        },
    )

    return response


def test_build():
    ## update build, check build flag
    current_build_number = int(update_build(package=package)[5:])
    output = run_pipeline_till_success()
    assert output["package"] == package
    assert output["deployed_flag"] == False
    assert output["build_flag"] == True
    new_build_number = int(get_latest_build(package=package)[5:])
    assert new_build_number == (current_build_number + 1)


def test_deploy():
    # update deploy in ap-southeast-1 check deploy flag
    current_layer_version = int(update_layer(package=package, region=region))
    output = run_pipeline_till_success()
    assert output["package"] == package
    assert output["deployed_flag"] == True
    assert output["build_flag"] == False
    assert output["deployed_to"][0] == region
    new_layer_version = get_latest_layer_version(package=package, region=region)
    assert new_layer_version == (current_layer_version + 1)

    ## Check latest layer
    latest = get_layer_record(new_layer_version, package, region)
    assert "exDt" not in latest.keys()
    assert latest["dplySts"]["S"] == "latest"
    layer_arn = check_layer(latest["arn"]["S"])["LayerVersionArn"]
    assert layer_arn == latest["arn"]["S"]

    # Check Previous Layer
    latest = get_layer_record(current_layer_version, package, region)
    assert "exDt" in latest.keys()
    assert latest["dplySts"]["S"] == "deprecated"
    layer_arn = check_layer(latest["arn"]["S"])["LayerVersionArn"]
    assert layer_arn == latest["arn"]["S"]

    # Delete Layer
    deleted = delete_layer(current_layer_version, package, region)
    time.sleep(10)
    deleted_layer = get_layer_record(current_layer_version, package, region)
    assert "exDt" not in deleted_layer.keys()
    assert "dplySts" not in deleted_layer.keys()
    assert "dltdDt" in deleted_layer.keys()
    layer_arn = check_layer(deleted_layer["arn"]["S"])
    assert layer_arn is None


def test_do_nothing():
    # don't change anything
    output = run_pipeline_till_success()
    assert output["package"] == package
    assert output["deployed_flag"] == False
    assert output["build_flag"] == False
