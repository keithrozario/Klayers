import json
import os

import boto3
from aws_lambda_powertools.logging import Logger

from common.get_config_from_s3 import (
    download_packages_from_s3,
    download_python_versions_from_s3,
    download_regions_from_s3,
)

logger = Logger()

"""
Loads configuration from S3 into DynamoDB
Includes python_versions, packages, regions
Packages and regions are python_version specific (each python_version has its own regions/packages)
"""


@logger.inject_lambda_context
def main(event, context):
    """Args:
    event::dict
       calling_service::Service calling the load_config
       python_versions::optional list of python versions
    returns::dict
    """
    logger.info(event)
    event = event or {}
    body_data = {}
    if isinstance(event.get("body"), str):
        try:
            body_data = json.loads(event["body"]) or {}
        except (json.JSONDecodeError, TypeError):
            body_data = {}

    python_versions = (
        event.get("python_versions")
        or body_data.get("python_versions")
        or download_python_versions_from_s3()
    )

    # Load Python Versions
    response = load_config(
        python_version="all", config_type="pyVrsns", config_items=python_versions
    )
    logger.info(
        {
            "message": "Loaded python_versions",
            "python_versions": python_versions,
            "response": response,
        }
    )

    # Load Regions
    regions = download_regions_from_s3()
    logger.info({"message": "Regions in S3", "regions": regions})

    for python_version in python_versions:
        # Load Packages
        packages = download_packages_from_s3(python_version=python_version)
        response = load_config(
            python_version=python_version, config_type="pckgs", config_items=packages
        )
        logger.info(
            {
                "message": "Loaded packages",
                "python_version": python_version,
                "packages": packages,
                "response": response,
            }
        )

        # Load regions
        response = load_config(
            python_version=python_version, config_type="rgns", config_items=regions
        )
        logger.info(
            {
                "message": "Loaded regions",
                "python_version": python_version,
                "regions": regions,
                "response": response,
            }
        )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Loaded Config"}),
    }


def load_config(python_version: str, config_type: str, config_items: list) -> dict:
    """Args:
        python_version: Version of python (e.g. all, p3.8, p3.9, p3.13)
        config_type: What type of item (e.g. pyVrsns, rgns, pckgs)
        config_items: List of items to store in cnfg attribute

    Returns:
        response::dict
            python_version::str
            loaded_config::int
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DB_NAME"])
    response = table.put_item(
        Item={
            "pk": f"cnfg#{config_type}",
            "sk": python_version,
            "cnfg": config_items,
        }
    )
    logger.info(response)

    return {
        "python_version": python_version,
        "loaded_config": len(config_items),
    }
