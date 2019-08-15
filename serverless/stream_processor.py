import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main(event, context):

    print(event)

    return "Done"
