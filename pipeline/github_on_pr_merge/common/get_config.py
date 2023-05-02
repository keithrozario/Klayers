import os
import json

from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
import requests


def get_from_common_service(
    resource: str, method: str = "GET", data: dict = None, headers: dict = None
):
    """
    Args:
        resource: The resource to get from the common service (e.g. /api/v1/config/python-version). Remember '/' at beginning
    Return:
        The json loaded response from the API
    """
    common_service_url = os.environ["COMMON_SERVICE_URL"]

    auth = BotoAWSRequestsAuth(
        aws_host=common_service_url.split("/")[2],
        aws_region=os.environ["AWS_REGION"],
        aws_service="execute-api",
    )

    if method == "GET":
        response = requests.get(f"{common_service_url}{resource}", auth=auth)
    elif method == "POST":
        response = requests.post(
            f"{common_service_url}{resource}", auth=auth, json=data, headers=headers
        )
    else:
        raise Exception(f"Method '{method}' not supported")

    if response.status_code != 200:
        raise Exception(
            f"Error {response.status_code} from common service: {response.content}"
        )
    else:
        result = json.loads(response.content)

    return result
