import os
import json
import boto3
import requests

from aws_lambda_powertools.logging import Logger
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

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

    common_service_url = os.environ["COMMON_SERVICE_URL"]
    python_versions = get_python_versions(url=common_service_url)['python_versions']
    logger.info(f"Python Versions: {python_versions}")

    return python_versions

def get_python_versions(url: str):
    auth = BotoAWSRequestsAuth(
        aws_host=url.split("/")[2],
        aws_region=os.environ['AWS_REGION'],
        aws_service='execute-api'
    )
    
    response = requests.get(
        f"{url}/api/v1/python-versions",
        auth=auth
    )
    return json.loads(response.content)