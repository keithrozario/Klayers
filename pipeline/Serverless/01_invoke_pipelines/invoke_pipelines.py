import json
import os
import boto3
from aws_lambda_powertools.logging import Logger

logger = Logger()

from common.get_config import get_from_common_service


@logger.inject_lambda_context
def main(event, context):
    """
    Args:
      package: Python Package to build and deploy
    return:
      response: Entries in EventBridge for processing
    """

    client = boto3.client("events")
    python_versions = get_from_common_service(resource="/api/v1/python-versions")
    logger.info(f"Python Versions: {python_versions}")

    for python_version in python_versions:
        packages = get_from_common_service(
            resource=f"/api/v1/config/{python_version}/pckgs"
        )
        logger.info(f"{packages}")

        # post message to EventBridge to trigger step functions
        seconds_delay = 30  # Start with no delay
        seconds_interval = 30  # Increment it by 30 seconds
        parallel_executions_between_delays = (
            2  # Every 2 executions **PER** python version
        )
        for i, package in enumerate(packages):
            if (i + 1) % parallel_executions_between_delays == 0:
                seconds_delay += seconds_interval

            entry = {
                "Source": f"Klayers.invoke.{os.environ['STAGE']}",
                "Resources": [],
                "DetailType": "invoke_pipeline",
                "Detail": json.dumps(
                    {
                        "package": package,
                        "python_version": python_version,
                        "force_build": False,
                        "force_deploy": False,
                        "secondsDelay": seconds_delay,
                    }
                ),
                "EventBusName": "default",
            }
            logger.info(entry)
            client.put_events(Entries=[entry])

    return python_versions
