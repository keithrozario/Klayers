import os
import json
import time

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
        null
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
      package: Python Package to build and deploy
    return:
      response: Entries in EventBridge for processing
    """

    client = boto3.client("events")
    stage = os.environ["STAGE"]

    for python_version in ["p3.8", "p3.9"]:
        packages = get_config_items(config_type="pckgs", python_version=python_version)
        entries = []
        logger.info(f"Preparing {len(packages)} packages")
        # post message to EventBridge to trigger step functions
        for package in packages:

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
                    }
                ),
                "EventBusName": "default",
            }
            response = client.put_events(Entries=[entry])
            log_eventbridge_errors(response, logger)
            ### Anti-patternt to put time.sleep(1) above -- but will implement SQS in the next release ###
            time.sleep(2)

        ### Had to Remve this section, as dumping 10 messages into Event bridge, caused congestion issues when invoking lambda in step functions ###
        # maximum 10 entries per put_events API call
        # chunk_10 = [entries[i : i + 10] for i in range(0, len(entries), 10)]
        # for chunk in chunk_10:
        #     response = client.put_events(Entries=chunk)
        #     log_eventbridge_errors(response, logger)

        # Post Status to Slack
        message = f"Started build on {len(packages)} packages for {python_version}"
        entry = {
            "Source": f"Klayers.invoke.{stage}",
            "Resources": [],
            "DetailType": "post_to_slack",
            "Detail": json.dumps({"message": message}),
            "EventBusName": "default",
        }
        slack_response = client.put_events(Entries=[entry])
        log_eventbridge_errors(slack_response, logger)

    return None
