from aws_lambda_powertools.logging import Logger
from common.get_config import get_from_common_service

logger = Logger()


@logger.inject_lambda_context
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

    response = get_from_common_service(resource="/api/v1/load-config", method="POST")
    logger.info(response)

    return event
