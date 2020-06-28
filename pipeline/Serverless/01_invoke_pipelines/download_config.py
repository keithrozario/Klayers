import os
import csv
import io
import hashlib

import requests

import boto3
from aws_lambda_powertools.logging import Logger

logger = Logger()


@logger.inject_lambda_context
def download_config_from_github(event, context):

    """
    Download Config from GitHub
    """

    repo_name_branch = "keithrozario/Klayers/master"
    stage = os.environ["STAGE"]
    bucket_name = os.environ["BUCKET_NAME"]
    base_url = (
        f"https://raw.githubusercontent.com/{repo_name_branch}/pipeline/config/{stage}"
    )

    filenames = ["packages.csv"]
    return_status = {}

    for config_file in filenames:

        config_url = f"{base_url}/{config_file}"
        return_status["url"] = config_url
        logger.info(f"Requesting latest config from {config_url}")
        response = requests.get(config_url)

        # Sanity check on csv file
        file_as_string = response.content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(file_as_string))
        packages = [line["Package_Name"] for line in csv_reader]
        if len(packages) > 2:
            logger.info("CSV is valid")
        else:
            logger.error(f"{config_file} does not appear to be valid CSV")
            logger.info(file_as_string)
            return_status["status"] = f"Invalid CSV format at {config_url}"
            return return_status

        # Check eTag vs. md5
        hash_md5 = hashlib.md5(response.content).hexdigest()
        return_status["new_hash"] = hash_md5
        s3 = boto3.resource("s3")
        object_summary = s3.ObjectSummary(bucket_name, f"config/{config_file}")
        object_hash = object_summary.e_tag[
            1:-1
        ]  # e_tag is surrounded by double-quotes '"'
        return_status["old_hash"] = object_hash

        # upload only if file changed
        if hash_md5 == object_hash:
            logger.info("Config file unchanged, ignoring")
            return_status["status"] = "Config file unchanged, ignoring download"
        else:
            logger.info(f"current hash:{object_summary.e_tag}")
            file_obj = io.BytesIO(response.content)
            s3 = boto3.client("s3")
            s3.upload_fileobj(
                file_obj, os.environ["BUCKET_NAME"], f"config/{config_file}"
            )
            logger.info(f"Uploaded new config file with hash {hash_md5}")
            return_status["status"] = "Uploaded new config file"

    return return_status
