import json
import os
import csv
import io
import hashlib

import requests
import boto3
from aws_lambda_powertools.logging import logger_setup, logger_inject_lambda_context

logger = logger_setup()
base_url = "https://raw.githubusercontent.com/keithrozario/Klayers/master/pipeline/config"


@logger_inject_lambda_context
def push_master(event, context):

    """
    A push to master occurred
    """

    stage = os.environ['STAGE']
    bucket_name = os.environ['BUCKET_NAME']
    filenames = ['packages.csv']

    for config_file in filenames:

        config_url = f"{base_url}/{stage}/{config_file}"
        logger.info(f"Requesting latest config from {config_url}")
        response = requests.get(config_url)

        # Sanity check on csv file
        file_as_string = response.content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(file_as_string))
        packages = [line['Package_Name'] for line in csv_reader]
        if len(packages) > 1:
            logger.info("File looks to be valid CSV")
        else:
            logger.error("File does not appear to be valid CSV")
            exit(1)

        # Check eTag vs. md5
        hash_md5 = hashlib.md5(response.content).hexdigest()
        s3 = boto3.resource('s3')
        object_summary = s3.ObjectSummary(bucket_name, f'config/{config_file}')

        # upload only if file changed
        if hash_md5 == object_summary.e_tag[1:-1]:  # e_tag is surrounded by double-quotes '"'
            logger.info("File unchanged, ignoring")
        else:
            logger.info(f"current hash:{object_summary.e_tag}")
            file_obj = io.BytesIO(response.content)
            s3 = boto3.client('s3')
            s3.upload_fileobj(file_obj, os.environ['BUCKET_NAME'], f'config/{config_file}')
            logger.info(f"Uploaded new config file with hash {hash_md5}")

    return 0

