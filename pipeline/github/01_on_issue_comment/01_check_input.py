import json
import boto3
import datetime
from aws_lambda_powertools.logging import Logger

logger = Logger()

@logger.inject_lambda_context
def main(event, context):
    logger.info(event)
    return {
        "version": "0",
        "id": "gh-comment-id-ID",
        "detail-type": "invoke_pipeline",
        "source": "gh-check-input",
        "time": datetime.datetime.utcnow().isoformat(),
        "resources": [],
        "detail": {
            "package": "idna",
            "python_version": "p3.9",
            "force_build": False,
            "force_deploy": False
        }
    }