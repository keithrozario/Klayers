import os
import json

from aws_lambda_powertools.logging import logger_setup, logger_inject_lambda_context
import slack
import boto3

"""
Cold start code
"""
logger = logger_setup()

ssm_client = boto3.client('ssm')
response = ssm_client.get_parameter(
    Name=os.environ.get('SLACK_TOKEN_PARAMETER'),
    WithDecryption=True
)
slack_token = response.get('Parameter').get('Value')
client = slack.WebClient(token=slack_token)


@logger_inject_lambda_context
def slack_notification(event, context):

    message = event['message']
    channel = f"buildstatus-{os.environ['STAGE'][8:][:-3]}"

    status = post_to_slack(message=message,
                           channel=channel)

    if status:
        logger.info(f"Successfully posted {message} to {channel}")
        status = "Success"
    else:
        logger.error(f"Failed to post {message} to {channel}")
        status = "Failed"

    return json.dumps({"status": status})


def post_to_slack(message, channel):

    response = client.chat_postMessage(channel=channel,
                                       text=message)

    return response['ok']