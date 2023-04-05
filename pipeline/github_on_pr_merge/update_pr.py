from aws_lambda_powertools.logging import Logger

logger = Logger()


@logger.inject_lambda_context
def main(event, context):
    """
    Args:
     event::tuple(2)
        package:: dict
            python_version::string (e.g. p3.8)
            python_package::list list of packages that were deployed
        pr_number::dict
            pr_number::int PR Number associated with this event
    """

    ## TO DO ##

    return None
