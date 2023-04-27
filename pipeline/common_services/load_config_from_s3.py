import os
import boto3
import json
from aws_lambda_powertools.logging import Logger
from common.get_config_from_s3 import download_packages_from_s3

logger = Logger()
dynamodb = boto3.resource("dynamodb")

def main(event, context):
    """
    Args:
     event::dict
        python_versions::list of python_versions
     returns::dict
    """
    logger.debug(event)
    python_versions = event['python_versions']
    responses = []
    for python_version in python_versions:
        response = load_config(python_version=python_version, config_type="rgns")
        responses.append(response)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(responses),
    }

def load_config(python_version: str, config_type: str) -> dict:
    """
    Args:
        python_version: Version of python (e.g. p3.8, p3.9)
        config_type: What type of item (e.g. rgns, pckgs) remember the 's'
    Returns:
        response::dict
            python_version::str
            num_packages::int
    """

    logger.info(
        f"Putting Dynamo Item type: {config_type} for python_version: {python_version}"
    )
    packages = download_packages_from_s3(python_version=python_version)
    logger.info(f"Number of packages: {len(packages)}")
    table = dynamodb.Table(os.environ["DB_NAME"])
    response = table.put_item(
        Item={
            "pk": f"cnfg#{config_type}",
            "sk": python_version,
            "cnfg": packages,
        }
    )
    logger.info(response)
    return {
        "python_version": python_version,
        "num_packages": len(packages),
    }
