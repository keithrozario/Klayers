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
def slack_notification_pipeline_error(event, context):

    """
    Post error messages for various failed statuses of Pipeline step function to slack
    event: see https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
    """

    status = event.get('detail', {}).get('status')
    package = json.loads(event.get('detail', {}).get('input')).get('package')

    status = post_to_slack(message=f"ERROR: Building {package} status: {status}",
                           channel=channel)

    return json.dumps({"status": status})


@logger_inject_lambda_context
def slack_notification_publish(event, context):

    """
    Post status of publish state machine to Slack
    event: see https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
    """

    status = event.get('detail', {}).get('status')

    if status in ['TIMED_OUT', 'ABORTED', 'FAILED']:
        message = f"ERROR: Publishing to Github failed"
    elif status == 'SUCCEEDED':
        message = f"GOOD: Build Complete, Published to Github complete"
    else:
        message = f"Publish Complete, but unknown state"

    status = post_to_slack(message=message,
                           channel=channel)

    return json.dumps({"status": status})


@logger_inject_lambda_context
def post_to_slack(message, channel):

    response = client.chat_postMessage(channel=channel,
                                       text=message)

    if response['ok']:
        logger.info(f"Successfully posted {message} to {channel}")
        status = "Success"
    else:
        logger.error(f"Failed to post Message:{message} to Channel:#{channel}")
        status = "Failed"

    return status