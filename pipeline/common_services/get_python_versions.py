import json
from aws_lambda_powertools.logging import Logger

from common.get_config import get_config_items

logger = Logger()


@logger.inject_lambda_context
def main(event, context):
    """
    Returns a list of all python versions currently supported

    Args: None
    Return:
        python_versions : List of python versions e.g. ["p3.8","p3.9","p3.10-arm64"]
    """
    status_code = 200
    try:
        python_versions = get_config_items(python_version="all", config_type="pyVrsns")
        logger.info(python_versions)
        return_value = python_versions
    except KeyError:  # no items in db
        return_value = {"message": "No items in DB, have you loaded config yet?"}
        status_code = 500

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(return_value),
    }
