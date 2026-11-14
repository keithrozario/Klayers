import json
import os
import time

import boto3
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

_cached_url: str | None = None
_cached_time: float = 0.0


def get_common_service_url() -> str:
    """Resolves CommonServiceApi URL dynamically from env or SSM with 300s in-memory cache."""
    global _cached_url, _cached_time

    env_url = os.environ.get("COMMON_SERVICE_URL")
    if env_url:
        return env_url.rstrip("/")

    now = time.time()
    if _cached_url is not None and (now - _cached_time < 300):
        return _cached_url

    stage = os.environ["STAGE"]
    ssm = boto3.client("ssm")
    param_name = f"/common-service/{stage}/CommonServiceApi/URL"
    resp = ssm.get_parameter(Name=param_name)
    url = resp["Parameter"]["Value"].rstrip("/")
    _cached_url = url
    _cached_time = now
    return url


def get_from_common_service(resource: str, method: str = "GET", data: dict | None = None, headers: dict | None = None):
    """Args:

        resource: The resource to get from the common service (e.g. /api/v1/config/python-version). Remember '/' at beginning
    Return:
        The json loaded response from the API
    """
    common_service_url = get_common_service_url()

    auth = BotoAWSRequestsAuth(
        aws_host=common_service_url.split("/")[2],
        aws_region=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")),
        aws_service="execute-api",
    )
    request_url = f"{common_service_url}{resource}"

    if method == "GET":
        response = requests.get(request_url, auth=auth)
    elif method == "POST":
        response = requests.post(request_url, auth=auth, json=data, headers=headers)
    else:
        raise ValueError(f"Method '{method}' not supported")

    if response.status_code != 200:
        raise RuntimeError(f"Error {response.status_code} from common service: {response.content}")
    else:
        result = json.loads(response.content)

    return result
