import json

from aws_lambda_powertools.logging import Logger

from common.get_config import get_config_items

logger = Logger()


@logger.inject_lambda_context
def main(event, context):
    """Returns config items for a given python version and config type

    Args:
        python_version: Python version to get config items for
        config_type: The type of configuration required (e.g. pckgs, rgns)
    Return:
        config_items: List of config items
    """
    path_parameters = event.get("pathParameters") or {}
    python_version = path_parameters.get("python_version")
    config_type = path_parameters.get("config_type")

    config_items = get_config_items(python_version=python_version, config_type=config_type)
    logger.info(get_config_items.cache_info())

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(config_items),
    }
