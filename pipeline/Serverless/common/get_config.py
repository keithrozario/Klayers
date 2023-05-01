import os
import json

from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
import requests


def get_from_common_service(resource: str):
    """
    Args:
        resource: The resource to get from the common service (e.g. /api/v1/config/python-version). Remember '/' at beginning
    Return:
        The json loaded response from the API
    """
    common_service_url = os.environ["COMMON_SERVICE_URL"]

    auth = BotoAWSRequestsAuth(
        aws_host=common_service_url.split("/")[2],
        aws_region=os.environ['AWS_REGION'],
        aws_service='execute-api'
    )
    
    response = requests.get(
        f"{common_service_url}{resource}",
        auth=auth
    )
    return json.loads(response.content)

