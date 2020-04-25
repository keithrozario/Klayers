import os
import json

import boto3

import get_config
from aws_lambda_powertools.logging import logger_setup, logger_inject_lambda_context
logger = logger_setup(service_name="Invoke Pipelines")


def log_eventbridge_errors(response, function_logger):
    """
    Args:
          response: Response from putting events onto eventBridge
          function_logger: logger to write out errors to (if any exists)
    return:
        null
    """

    if response['FailedEntryCount'] > 0:
        for entry in response['Entries']:
            if entry.get('ErrorCode', False):
                logger.error(entry)
    return


@logger_inject_lambda_context
def main(event, context):

    """
    Args:
      package: Python Package to build and deploy
    return:
      response: Entries in EventBridge for processing
    """

    packages = get_config.get_packages()
    client = boto3.client('events')
    stage = os.environ['STAGE']

    entries = []
    logger.info(f"Preparing {len(packages)} packages")

    # post message to EventBridge to trigger step functions
    for package in packages:

        entry = {
            'Source': f"Klayers.invoke.{stage}",
            'Resources': [],
            'DetailType': "invoke_pipeline",
            'Detail': json.dumps({"package": package}),
            'EventBusName': 'default'
        }
        entries.append(entry)
    response = client.put_events(Entries=entries)
    log_eventbridge_errors(response, logger)

    # Post Status to Slack
    message = f"Started build on {len(packages)} packages, with {response['FailedEntryCount']} errors"
    entry = {
        'Source': f"Klayers.invoke.{stage}",
        'Resources': [],
        'DetailType': "post_to_slack",
        'Detail': json.dumps({"message": message}),
        'EventBusName': 'default'
    }
    slack_response = client.put_events(Entries=[entry])
    log_eventbridge_errors(slack_response, logger)

    return response
