import os
import json

import boto3
from aws_lambda_powertools.logging import Logger

logger = Logger()

from common.get_config import get_config_items


def log_eventbridge_errors(response: dict, function_logger: Logger):
    """
    Args:
          response: Response from putting events onto eventBridge
          function_logger: logger to write out errors to (if any exists)
    return:
        None
    """

    if response["FailedEntryCount"] > 0:
        for entry in response["Entries"]:
            if entry.get("ErrorCode", False):
                function_logger.error(entry)

    return None


@logger.inject_lambda_context
def main(event, context):
    """
    Args:
      event: list of dict. e.g. {"python_version": str, "new_packages": list}
    """

    for item in event:
        invoke_pipelines(
            packages=item["new_packages"], python_version=item["python_version"]
        )

    return event


def invoke_pipelines(packages: list, python_version: str):
    """
    Args:
        packages: List of packages to build
        python_version: Str of python version (e.g. p3.8, p3.9)
    return:
        None
    """
    client = boto3.client("events")
    stage = os.environ["STAGE"]

    logger.info(f"Preparing {len(packages)} packages")
    # post message to EventBridge to trigger step functions
    for i, package in enumerate(packages):
        entry = {
            "Source": f"Klayers.invoke.{stage}",
            "Resources": [],
            "DetailType": "invoke_pipeline",
            "Detail": json.dumps(
                {
                    "package": package,
                    "python_version": python_version,
                    "force_build": False,
                    "force_deploy": False,
                    "secondsDelay": 5*i,
                }
            ),
            "EventBusName": "default",
        }
        response = client.put_events(Entries=entry)

    return None
