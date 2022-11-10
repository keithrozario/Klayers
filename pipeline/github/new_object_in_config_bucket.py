import json
import boto3
from aws_lambda_powertools.logging import Logger

from common.get_config import get_config_items

logger = Logger()

@logger.inject_lambda_context
def main(event, context):
    logger.info(event)
    for python_version in ["p3.8", "p3.9"]:
        packages = get_config_items(config_type="pckgs", python_version=python_version)
    return packages