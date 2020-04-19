import json

import requests

import boto3
from aws_lambda_powertools.logging import logger_setup, logger_inject_lambda_context
logger = logger_setup()


@logger_inject_lambda_context
def push_master(event, context):

    """
    Receive all webhooks on master from EventBridge
    """

    print(event)

    return True


@logger_inject_lambda_context
def test_event(event,context):

    client = boto3.client('events')
    response = client.put_events(
        Entries=[
            {
                'Source': "github.webhook",
                'Resources': [],
                'DetailType': 'push',
                'Detail': json.dumps({"ref": "refs/heads/master"}),
                'EventBusName': 'default'
            },
        ]
    )

    if response['FailedEntryCount'] == 0:
        return "No Errors Detected"
    else:
        return "Error"

