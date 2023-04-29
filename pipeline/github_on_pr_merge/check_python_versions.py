import os
import json
import boto3
import requests

from aws_lambda_powertools.logging import Logger
from common.get_config import get_from_common_service 
 


logger = Logger()
s3 = boto3.client("s3")
config_file = "config.json"  # config file in the config bucket, (pipeline/config/config.json in repo)


@logger.inject_lambda_context
def main(event, context):
    """
    Args: None
    Return:
        python_versions : List of python versions e.g. ["p3.8","p3.9"]
    """

    python_versions = get_from_common_service(resource="/api/v1/python-versions")['python_versions']
    logger.info(f"Python Versions: {python_versions}")

    return python_versions

