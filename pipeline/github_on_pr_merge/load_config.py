import os
import boto3
from aws_lambda_powertools.logging import Logger
from common.get_config_from_s3 import download_packages_from_s3

logger = Logger()
dynamodb = boto3.resource("dynamodb")

def main(event, context):
    """
    Args:
     event::tuple(2)
        package:: list(dict)
            python_version::string (e.g. p3.8)
            python_package::list list of packages that were deployed
        pr_number::dict
            pr_number::int PR Number associated with this event
    """
    logger.info("hello")
    logger.info(event)
    for elem in event[0]:
        python_version = elem['python_version']
        load_config(python_version=python_version, config_type='pckgs')

    return event

def load_config(
    python_version: str, config_type: str
) -> dict:
    """
    Args:
        python_version: Version of python (e.g. p3.8, p3.9)
        config_type: What type of item (e.g. rgns, pckgs) remember the 's'
    Returns: None
    """

    logger.info(
        f"Putting Dynamo Item type: {config_type} for python_version: {python_version}"
    )
    packages = download_packages_from_s3(python_version=python_version)
    logger.info(f"Number of packages: {len(packages)}")
    table = dynamodb.Table(os.environ["DB_NAME"])
    response = table.put_item(
        Item={
            "pk": f"cnfg#{config_type}",
            "sk": python_version,
            "cnfg": packages,
        }
    )
    logger.info(response)
    return response