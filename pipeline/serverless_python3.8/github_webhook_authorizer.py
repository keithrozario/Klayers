import os
import hmac
import hashlib

from lambda_cache import ssm

import boto3
from aws_lambda_powertools.logging import logger_setup, logger_inject_lambda_context
logger = logger_setup()


def check_sig(payload, sig, secret):

    h1 = hmac.new(bytearray(secret, 'utf-8'),
                  bytearray(payload, 'utf-8'),
                  hashlib.sha1)

    if hmac.compare_digest(h1.hexdigest(), sig[5:]):
        logger.info("Verified signature, Proceeding")
        return True
    else:
        logger.error("Invalid Signature, terminating")
        exit(1)
        return False


@logger_inject_lambda_context
@ssm.cache(os.environ['GITHUB_SECRET_PARAM'])
def handler(event, context):

    """
    Receives a POST from github, verifies the signature before placing message onto eventhub.
    """
    headers = {'Access-Control-Allow-Origin': '*'}  # CORS

    secret = getattr(context, 'github_webhook_secret')
    github_event = event['headers']['X-GitHub-Event']
    sig = event['headers']['X-Hub-Signature']
    result = check_sig(event['body'], sig, secret)

    if result:
        client = boto3.client('events')
        response = client.put_events(
            Entries=[
                {
                    'Source': "github.webhook",
                    'Resources': [],
                    'DetailType': f'{github_event}',
                    'Detail': event['body'],
                    'EventBusName': 'default'
                },
            ]
        )
        if response['FailedEntryCount'] == 0:
            return {'statusCode': 202,
                    'headers': headers}
        else:
            logger.error(f"Unable to process {github_event}")
            return {'statusCode': 500,
                    'headers': headers}
    else:
        logger.error(f"Verification of {github_event} from Github failed!")
        return {'statusCode': 403,
                'headers': headers}




