from aws_lambda_powertools.logging import Logger
from common.get_config import get_from_common_service

logger = Logger()


@logger.inject_lambda_context
def main(event, context):
    """
    Args: None
    Return:
        python_versions : List of python versions e.g. ["p3.8","p3.9"]
    """

    python_versions = get_from_common_service(resource="/api/v1/python-versions")
    logger.info({"python_versions": python_versions, "event": event})
    return python_versions
