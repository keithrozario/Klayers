import os
import csv
import json
import boto3
from aws_lambda_powertools.logging import Logger
from common.get_config import get_from_common_service
from common.get_config_from_s3 import download_packages_from_s3

logger = Logger()


@logger.inject_lambda_context
def main(event, context) -> dict:
    """
    Args:
        event (Str): Python version to check for
    Return:
        python_version (Str): Python version as string (e.g. p3.8)
        new_packages (List): List of packages to be deployed
    """

    python_version = event  # based on step function
    logger.info({"python_version": python_version})

    packages_in_dynamo = get_from_common_service(
        resource=f"/api/v1/config/{python_version}/pckgs"
    )
    logger.info({f"packages_in_dynamo": packages_in_dynamo})

    packages_in_s3 = download_packages_from_s3(python_version=python_version)
    
    packages_in_s3_trim = [pckg.split("[")[0] for pckg in packages_in_s3]
    new_packages = [pckg for pckg in packages_in_s3_trim if pckg not in packages_in_dynamo]
    logger.info({"new_packages": new_packages})

    return {"python_version": python_version, "new_packages": new_packages}
