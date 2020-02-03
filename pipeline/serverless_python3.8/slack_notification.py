import os
import json

from aws_lambda_powertools.logging import logger_setup, logger_inject_lambda_context
import slack
import boto3

"""
Cold start code
"""
logger = logger_setup()
channel = f"#buildstatus-{os.environ['STAGE'][8:][:-3]}"

# Get Slack Token
ssm_client = boto3.client('ssm')
response = ssm_client.get_parameter(
    Name=os.environ.get('SLACK_TOKEN_PARAMETER'),
    WithDecryption=True
)
slack_token = response.get('Parameter').get('Value')
client = slack.WebClient(token=slack_token)


@logger_inject_lambda_context
def slack_notification_test(event, context):

    message = event['message']

    status = post_to_slack(message=message,
                           channel=channel)

    if status:
        logger.info(f"Successfully posted {message} to {channel}")
        status = "Success"
    else:
        logger.error(f"Failed to post Message:{message} to Channel:#{channel}")
        status = "Failed"

    return json.dumps({"status": status})


@logger_inject_lambda_context
def slack_notification_pipeline(event, context):

    """
    Post error messages for various failed statuses of Pipeline step function to slack
    event: see https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
    """

    status = event.get('detail', {}).get('status')
    package = json.loads(event.get('detail', {}).get('input')).get('package')

    if status in ['TIMED_OUT', 'ABORTED', 'FAILED']:
        message = f"ERROR: Building {package} status: {status}"
    elif status == 'SUCCEEDED':
        message = f"GOOD: Building {package} status: {status}"
    elif status == 'RUNNING':
        message = f"INFO: Building {package} status: {status}"
    else:
        message = f"Unknown Status {status}"

    status = post_to_slack(message=message,
                           channel=channel)

    if status:
        logger.info(f"Successfully posted {message} to {channel}")
        status = "Success"
    else:
        logger.error(f"Failed to post Message:{message} to Channel:#{channel}")
        status = "Failed"

    return json.dumps({"status": status})


def post_to_slack(message, channel):

    response = client.chat_postMessage(channel=channel,
                                       text=message)

    return response['ok']