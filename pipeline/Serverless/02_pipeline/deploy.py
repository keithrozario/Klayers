import os
import time
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from aws_lambda_powertools.logging import Logger

logger = Logger()

from common.get_config import get_from_common_service
from common.get_compatible import get_compatible_runtimes, get_compatible_architectures

dynamo_client = boto3.client("dynamodb")


def check_regions_to_deploy(
    package: str,
    requirements_hash: str,
    regions: list,
    python_version: str,
    force_deploy: bool,
) -> list:
    """
    Args:
        package: Name of package to deploy
        requirements_hash: Hash of requirements.txt file
        regions: Total regions configured to deployed
        python_version: version of python
    return:
        regions_to_deploy: Regions where latest package doesn't match requirements_hash provided
    """

    if force_deploy:
        return regions

    table_name = os.environ["DB_NAME"]
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    response = table.query(
        IndexName="package_global_by_python_version",
        KeyConditionExpression=Key("pckg#PyVrsn").eq(f"{package}:{python_version}")
        & Key("dplySts").eq("latest"),
    )

    # check if there are any region in regions that aren't deployed
    regions_deployed = [item["rgn"] for item in response["Items"]]
    regions_to_deploy = [region for region in regions if region not in regions_deployed]
    logger.info(
        {
            "message": f"Deploying to {len(regions_to_deploy)} new regions",
            "new_regions": regions_to_deploy,
            "regions_deployed": regions_deployed,
        }
    )

    # for all deployed regions, check if it has the latest version
    for item in response["Items"]:
        if item["rqrmntsHsh"] != requirements_hash:
            if item["rgn"] in regions:
                regions_to_deploy.append(item["rgn"])

    # deduplicate
    regions_to_deploy = list(set(regions_to_deploy))

    logger.info({"regions_to_deploy": regions_to_deploy})

    return regions_to_deploy


def download_artifact(zip_file_S3Key):
    """
    Downloads s3://bucket_name/zip_file_S3Key to /tmp directory
    Returns the full zip binary for easier upload
    """

    bucket_name = os.environ["BUCKET_NAME"]
    s3 = boto3.resource("s3")
    tmp_file_path = "/tmp/package.zip"

    logger.info(
        f"Downloading package from S3 : {zip_file_S3Key} to location: {tmp_file_path}"
    )
    s3.meta.client.download_file(bucket_name, zip_file_S3Key, tmp_file_path)
    logger.debug(f"Downloaded package from S3")
    with open(tmp_file_path, "rb") as zip_file:
        zip_binary = zip_file.read()

    return zip_binary


def get_requirements_txt(package: str, python_version: str) -> str:
    """
    Args:
        package: Name of package to query for
        python_version: Version fo python used (e.g. 3.9, 3.8, 3.10)
    return:
        requirements_txt: Requirements.txt of the package, or "null" if not present
    """

    build_v0 = f"bldVrsn0#{python_version}"
    sk = f"pckg#{package}"

    client = boto3.client("dynamodb")
    table_name = os.environ["DB_NAME"]
    response = client.get_item(
        TableName=table_name,
        Key={"pk": {"S": build_v0}, "sk": {"S": sk}},
    )
    logger.info({"query_requirements": response})
    requirements_txt = response.get("Item", {}).get("rqrmntsTxt", {}).get("S", "null")

    return requirements_txt


@logger.inject_lambda_context
def main(event, context):
    package = event["package"]
    version = event["version"]
    build_flag = event["build_flag"]
    zip_file_S3key = event["zip_file_S3key"]
    requirements_hash = event["requirements_hash"]
    license_info = event["license_info"]
    force_deploy = event["force_deploy"]
    table_name = os.environ["DB_NAME"]
    expiry_days = int(os.environ["EXPIRY_DAYS"])
    python_version = event["python_version"]

    regions = get_from_common_service(resource=f"/api/v1/config/{python_version}/rgns")
    logger.info({"regions": regions})

    deployed_flag = False
    # remove Optional dependencies from name to conform to Lambda Layer Arn naming requirements
    if "[" in package:
        package = package.split("[")[0]

    # Check if need to deploy
    regions_to_deploy = check_regions_to_deploy(
        package=package,
        requirements_hash=requirements_hash,
        regions=regions,
        python_version=python_version,
        force_deploy=force_deploy,
    )
    if len(regions_to_deploy) == 0:
        logger.info({"message": "No new regions to deploy to, terminating!"})
        return {
            "deployed_flag": deployed_flag,
            "build_flag": build_flag,
            "package": package,
            "version": version,
            "requirements_hash": requirements_hash,
        }

    logger.info(
        {"message": "Regions to deploy", "regions_to_deploy": regions_to_deploy}
    )

    layer_name = (
        f"{os.environ['LAMBDA_LAYER_PREFIX']}{python_version.replace('.','')}-{package}"
    )
    zip_binary = download_artifact(zip_file_S3key)

    requirements_txt = get_requirements_txt(
        package=package, python_version=python_version
    )

    for region in regions_to_deploy:
        # Publish Layer Version
        logger.info({"message": "Deploying", "region": region, "package": package})

        lambda_client = boto3.client("lambda", region_name=region)
        response = lambda_client.publish_layer_version(
            LayerName=layer_name,
            Description=f"{package}=={version} | {requirements_hash}",
            Content={"ZipFile": zip_binary},
            CompatibleRuntimes=get_compatible_runtimes(python_version=python_version),
            CompatibleArchitectures=get_compatible_architectures(
                python_version=python_version
            ),
            LicenseInfo=license_info,
        )
        layer_version_arn = response["LayerVersionArn"]
        layer_version_created_date = datetime.utcnow().isoformat()
        layer_version = int(layer_version_arn.split(":")[-1])

        # Make Layer Publicly accessible
        logger.info(
            {
                "message": "Making Public",
                "region": region,
                "package": package,
                "python_version": python_version,
                "arn": layer_version_arn,
                "created_date": layer_version_created_date,
            }
        )
        lambda_client.add_layer_version_permission(
            LayerName=layer_name,
            VersionNumber=layer_version,
            StatementId="make_public",
            Action="lambda:GetLayerVersion",
            Principal="*",
        )

        # Insert new entry into DynamoDB
        logger.info(
            {
                "message": "Inserting to table",
                "region": region,
                "package": package,
                "arn": layer_version_arn,
                "python_version": python_version,
            }
        )

        pk = f"lyr#{region}:{package}:{python_version}"
        sk_v0 = "lyrVrsn0#"
        # This version is different from the Lambda Layer Version -- this is the Klayer Version
        try:
            layer_version = dynamo_client.get_item(
                TableName=table_name,
                Key={
                    "pk": {"S": pk},
                    "sk": {"S": sk_v0},
                },
                ProjectionExpression="lyrVrsn",
            )["Item"]["lyrVrsn"]["N"]
            new_layer_version = int(layer_version) + 1
        except KeyError:
            new_layer_version = 1
        sk = f"lyrVrsn#v{new_layer_version}"
        sk_previous = f"lyrVrsn#v{new_layer_version-1}"

        dynamo_client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": table_name,
                        "Key": {
                            "pk": {"S": pk},
                            "sk": {"S": sk_v0},
                        },
                        "UpdateExpression": "set "
                        "rqrmntsTxt = :rqrmntsTxt, "
                        "pckgVrsn = :pckgVrsn, "
                        "rqrmntsHsh = :rqrmntsHsh,"
                        "arn = :arn,"
                        "crtdDt = :crtdDt,"
                        "lyrVrsn = :lyrVrsn,"
                        "pyVrsn = :pyVrsn",
                        "ExpressionAttributeValues": {
                            ":rqrmntsTxt": {"S": requirements_txt},
                            ":crtdDt": {"S": layer_version_created_date},
                            ":pckgVrsn": {"S": version},
                            ":rqrmntsHsh": {"S": requirements_hash},
                            ":arn": {"S": layer_version_arn},
                            ":lyrVrsn": {"N": str(new_layer_version)},
                            ":pyVrsn": {"S": python_version},
                        },
                        # Allow update only if
                        # Current lyrVrsn is less than updated value
                        # or lyrVrsn doesn't exists
                        "ConditionExpression": "lyrVrsn <= :lyrVrsn OR attribute_not_exists(lyrVrsn)",
                    }
                },
                {
                    "Put": {
                        "TableName": table_name,
                        "Item": {
                            "pk": {"S": pk},
                            "sk": {"S": sk},
                            "pckgVrsn": {"S": version},
                            "crtdDt": {"S": layer_version_created_date},
                            "rqrmntsTxt": {"S": requirements_txt},
                            "rqrmntsHsh": {"S": requirements_hash},
                            "arn": {"S": layer_version_arn},
                            "pckg": {"S": package},
                            "rgn": {"S": region},
                            "dplySts": {"S": "latest"},
                            "lyrVrsn": {"N": str(new_layer_version)},
                            "pyVrsn": {"S": python_version},
                            "rgn#PyVrsn": {"S": f"{region}:{python_version}"},
                            "pckg#PyVrsn": {"S": f"{package}:{python_version}"},
                        },
                    }
                },
            ]
        )
        if new_layer_version > 1:
            logger.info(
                {
                    "message": "Updating Expiry on previous version",
                    "region": region,
                    "package": package,
                    "arn": layer_version_arn,
                }
            )
            try:
                dynamo_client.update_item(
                    TableName=table_name,
                    Key={"pk": {"S": pk}, "sk": {"S": sk_previous}},
                    UpdateExpression="set " "dplySts = :dplySts, " "exDt = :exDt",
                    ExpressionAttributeValues={
                        ":dplySts": {"S": "deprecated"},
                        ":exDt": {"N": str(int(time.time() + 24 * 3600 * expiry_days))},
                    },
                    ConditionExpression="attribute_exists(sk)",
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    logger.warning(
                        {
                            "message": "Conditional Check failed",
                            "new_layer_version": new_layer_version,
                            "sk_previous": sk_previous,
                        }
                    )
        deployed_flag = True

    return {
        "deployed_to": regions_to_deploy,
        "deployed_flag": deployed_flag,
        "build_flag": build_flag,
        "package": package,
        "version": version,
        "requirements_hash": requirements_hash,
        "python_version": python_version,
    }
