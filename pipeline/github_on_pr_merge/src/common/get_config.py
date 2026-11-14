import json
import os
import time

import boto3
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

_CACHED_URL: str | None = None
_CACHED_TIME: float = 0.0
_CACHE_TTL: float = 300.0


def reset_url_cache() -> None:
    """Reset the module-level URL cache (useful for testing)."""
    global _CACHED_URL, _CACHED_TIME
    _CACHED_URL = None
    _CACHED_TIME = 0.0


def get_common_service_url() -> str:
    """Resolve the Common Service API URL.

    Checks os.environ['COMMON_SERVICE_URL'] first (e.g. for local tests).
    Otherwise, reads /common-service/{STAGE}/CommonServiceApi/URL from SSM
    and caches it for 300 seconds.
    """
    global _CACHED_URL, _CACHED_TIME

    env_url = os.environ.get("COMMON_SERVICE_URL")
    if env_url:
        return env_url.rstrip("/")

    now = time.time()
    if _CACHED_URL and (now - _CACHED_TIME) < _CACHE_TTL:
        return _CACHED_URL

    stage = os.environ["STAGE"]
    param_name = f"/common-service/{stage}/CommonServiceApi/URL"
    region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    ssm = boto3.client("ssm", region_name=region)
    response = ssm.get_parameter(Name=param_name)
    url = response["Parameter"]["Value"].rstrip("/")

    _CACHED_URL = url
    _CACHED_TIME = now
    return _CACHED_URL


def get_from_common_service(
    resource: str,
    method: str = "GET",
    data: dict | None = None,
    headers: dict | None = None,
):
    """Args:
        resource: The resource to get from the common service (e.g. /api/v1/config/python-version).
                  Remember '/' at beginning.
        method: HTTP method ("GET" or "POST").
        data: Optional payload for POST requests.
        headers: Optional headers.

    Return:
        The json loaded response from the API.
    """
    common_service_url = get_common_service_url()

    host = common_service_url.split("/")[2]
    region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

    auth = BotoAWSRequestsAuth(
        aws_host=host,
        aws_region=region,
        aws_service="execute-api",
    )

    if method == "GET":
        response = requests.get(f"{common_service_url}{resource}", auth=auth)
    elif method == "POST":
        response = requests.post(
            f"{common_service_url}{resource}", auth=auth, json=data, headers=headers
        )
    else:
        raise ValueError(f"Method '{method}' not supported")

    if response.status_code != 200:
        err_msg = response.content.decode("utf-8", errors="replace")
        raise RuntimeError(f"Error {response.status_code} from common service: {err_msg}")

    return json.loads(response.content)
