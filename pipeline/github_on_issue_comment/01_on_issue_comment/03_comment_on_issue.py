import json
import boto3
from aws_lambda_powertools.logging import Logger

logger = Logger()

@logger.inject_lambda_context
def main(event, context):
    logger.info(event)
    return None