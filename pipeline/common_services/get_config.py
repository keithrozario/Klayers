import json
from aws_lambda_powertools.logging import Logger

from common.get_config import get_config_items

logger = Logger()


@logger.inject_lambda_context
def main(event, context):
    """
    Returns a list of all python versions currently supported

    Args:
        python_version: Python version to get config items for
        config_type: The type of configuration required (e.g. pckgs, rgns)
    Return:
        config_items: List of config items
    """

    python_version = event.get("pathParameters").get("python_version")
    config_type = event.get("pathParameters").get("config_type")

    config_items = get_config_items(
        python_version=python_version, config_type=config_type
    )
    logger.info(get_config_items.cache_info())

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(config_items),
    }
