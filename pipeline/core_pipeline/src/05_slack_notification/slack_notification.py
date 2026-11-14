import json
import os

import boto3
from aws_lambda_powertools.logging import Logger
from slack_sdk import WebClient

logger = Logger()

_slack_client: WebClient | None = None
_default_channel: str | None = None


def _get_slack_client_and_channel() -> tuple[WebClient, str]:
    """Lazily initialize Slack WebClient and channel from SSM/env, cached in memory."""
    global _slack_client, _default_channel
    if _slack_client is not None and _default_channel is not None:
        return _slack_client, _default_channel

    stage = os.environ.get("STAGE", "Klayers-defaultp38")
    channel_suffix = stage[8:][:-3] if len(stage) > 11 else stage
    _default_channel = f"#buildstatus-{channel_suffix}"

    token_param = os.environ.get("SLACK_TOKEN_PARAMETER", f"/kl/{stage}/slack_token")
    ssm_client = boto3.client("ssm")
    response = ssm_client.get_parameter(Name=token_param, WithDecryption=True)
    slack_token = response.get("Parameter", {}).get("Value", "")
    _slack_client = WebClient(token=slack_token)
    return _slack_client, _default_channel


def post_to_slack(message: str, channel: str | None = None) -> str:
    client, default_chan = _get_slack_client_and_channel()
    target_channel = channel or default_chan
    response = client.chat_postMessage(channel=target_channel, text=message)

    if response.get("ok"):
        logger.info(f"Successfully posted Message:{message} to Channel:#{target_channel}")
        status = "Success"
    else:
        logger.error(f"Failed to post Message:{message} to Channel:#{target_channel}")
        status = "Failed"

    return status


@logger.inject_lambda_context
def slack_notification_pipeline_error(event, context):
    """Post error messages for various failed statuses of Pipeline step function to slack.

    event: see https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
    """
    status = event.get("detail", {}).get("status")
    package = json.loads(event.get("detail", {}).get("input", "{}")).get("detail", {}).get("package")

    status_res = post_to_slack(message=f"ERROR: Building {package} status: {status}")

    return json.dumps({"status": status_res})


@logger.inject_lambda_context
def slack_notification_invoke_pipeline_error(event, context):
    """Post error messages for various failed statuses of Pipeline step function to slack.

    event: see https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
    """
    status = event.get("detail", {}).get("status")

    if status in ["TIMED_OUT", "ABORTED", "FAILED"]:
        message = "ERROR: Invoking Pipelines"
    else:
        message = "ERROR: Unknown State of Publish"

    slack_status = post_to_slack(message)

    return json.dumps({"status": slack_status})


@logger.inject_lambda_context
def slack_notification_publish(event, context):
    """Post status of publish state machine to Slack.

    event: see https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
    """
    status = event.get("detail", {}).get("status", False)

    if status in ["TIMED_OUT", "ABORTED", "FAILED"]:
        message = f"ERROR: Publishing to Github failed with Status:{status}"
    elif status == "SUCCEEDED":
        message = "GOOD: Completed this week's build, posted to Github: https://github.com/keithrozario/Klayers"
    else:
        message = "ERROR: Unknown State of Publish"

    status_res = post_to_slack(message)

    return json.dumps({"status": status_res})


@logger.inject_lambda_context
def post_message_to_slack(event, context):
    """Generic Slack notifications via EventBridge."""
    message = event.get("detail", {}).get("message", False)

    if message:
        response = post_to_slack(message)
        logger.debug({"message": message, "response": response})
