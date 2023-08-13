import os
import boto3
import json
from aws_lambda_powertools.logging import Logger
from common.get_config_from_s3 import (
    download_packages_from_s3,
    download_regions_from_s3,
    download_python_versions_from_s3,
)

logger = Logger()
dynamodb = boto3.resource("dynamodb")

"""
Loads configuration from S3 into DynamoDB
Includes python_versions, packages, regions
Packages and region are python_version specific (each python_version has its own regions/packages)
"""


@logger.inject_lambda_context
def main(event, context):
    """
    Args:
     event::dict
        calling_service::Service calling the load_config
     returns::dict
    """

    logger.info(event)
    python_versions = event.get("python_versions", download_python_versions_from_s3())

    # Load Packages
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

    # regions
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
    """
    Args:
        python_version: Version of python (e.g. p3.8, p3.9, p3.11-arm64)
        config_type: What type of item (e.g. rgns, pckgs) remember the 's'
    Returns:
        response::dict
            python_version::str
            num_packages::int
    """

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
