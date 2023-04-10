import os
import json

import boto3
from aws_lambda_powertools.logging import Logger

logger = Logger()

import slack


"""
Cold start code
"""
default_channel = f"#buildstatus-{os.environ['STAGE'][8:][:-3]}"

# Get Slack Token
ssm_client = boto3.client("ssm")
response = ssm_client.get_parameter(
    Name=os.environ.get("SLACK_TOKEN_PARAMETER"), WithDecryption=True
)
slack_token = response.get("Parameter").get("Value")
client = slack.WebClient(token=slack_token)


@logger.inject_lambda_context
def slack_notification_pipeline_error(event, context):
    """
    Post error messages for various failed statuses of Pipeline step function to slack
    event: see https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
    """

    status = event.get("detail", {}).get("status")
    package = (
        json.loads(event.get("detail", {}).get("input"))
        .get("detail", {})
        .get("package")
    )

    status = post_to_slack(
        message=f"ERROR: Building {package} status: {status}", channel=default_channel
    )

    return json.dumps({"status": status})


@logger.inject_lambda_context
def slack_notification_invoke_pipeline_error(event, context):
    """
    Post error messages for various failed statuses of Pipeline step function to slack
    event: see https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
    """

    status = event.get("detail", {}).get("status")

    if status in ["TIMED_OUT", "ABORTED", "FAILED"]:
        message = f"ERROR: Invoking Pipelines"
    else:
        message = f"ERROR: Unknown State of Publish"

    slack_status = post_to_slack(message, default_channel)

    return json.dumps({"status": slack_status})


@logger.inject_lambda_context
def slack_notification_publish(event, context):
    """
    Post status of publish state machine to Slack
    event: see https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
    """

    status = event.get("detail", {}).get("status", False)

    if status in ["TIMED_OUT", "ABORTED", "FAILED"]:
        message = f"ERROR: Publishing to Github failed with Status:{status}"
    elif status == "SUCCEEDED":
        message = f"GOOD: Completed this week's build, posted to Github: https://github.com/keithrozario/Klayers"
    else:
        message = f"ERROR: Unknown State of Publish"

    status = post_to_slack(message, default_channel)

    return json.dumps({"status": status})


def post_to_slack(message, channel=default_channel):
    response = client.chat_postMessage(channel=channel, text=message)

    if response["ok"]:
        logger.info(f"Successfully posted Message:{message} to Channel:#{channel}")
        status = "Success"
    else:
        logger.error(f"Failed to post Message:{message} to Channel:#{channel}")
        status = "Failed"

    return status


@logger.inject_lambda_context
def post_message_to_slack(event, context):
    """
    Post status of publish state machine to Slack
    event: see https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
    """

    message = event.get("detail", {}).get("message", False)

    if message:
        response = post_to_slack(message, default_channel)
        logger.debug(
            {"message": message, "channel": default_channel, "response": response}
        )

    return None
