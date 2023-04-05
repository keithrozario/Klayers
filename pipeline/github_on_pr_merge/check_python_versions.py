import os
import csv
import json
import boto3
from aws_lambda_powertools.logging import Logger

logger = Logger()
s3 = boto3.client("s3")
config_file = "config.json"  # config file in the config bucket, (pipeline/config/config.json in repo)


@logger.inject_lambda_context
def main(event, context):
    """
    Args: None
    Return:
        python_versions : List of python versions e.g. ["p3.8","p3.9"]
    """

    s3.download_file(os.getenv("CONFIG_BUCKET"), config_file, f"/tmp/{config_file}")
    with open(f"/tmp/{config_file}", "r") as conf:
        config = json.loads(conf.read())

    python_versions = config["python_versions"]
    logger.info(python_versions)

    return python_versions
