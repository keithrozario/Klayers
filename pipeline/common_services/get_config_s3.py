import json
from aws_lambda_powertools.logging import Logger
from common.get_config_from_s3 import (
    download_packages_from_s3,
    download_regions_from_s3,
)

logger = Logger()


@logger.inject_lambda_context
def main(event, context):
    """
    Returns a list of all python versions currently supported

    Args:
        python_version: Python version to get config items for
        config_type: The type of configuration required (e.g. pckgs, rgns)
    Return:
        config_items: List of config items
    """

    python_version = event.get("pathParameters").get("python_version")
    config_type = event.get("pathParameters").get("config_type")

    if config_type == "pckgs":
        config_items = download_packages_from_s3(python_version=python_version)
    elif config_type == "rgns":
        config_items = download_regions_from_s3()
    else:
        config_items = []

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(config_items),
    }
