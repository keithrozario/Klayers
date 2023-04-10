import os
import json
import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools.logging import Logger
from common.dynamodb import map_keys

logger = Logger()


@logger.inject_lambda_context
def main(event, context):
    """
    Args:
        event.pathParameter.region: AWS region
        event.pathParameter.package: Python Package
        event.pathParameter.python_version: Python Version (e.g. p3.8, p3.9)
    returns:
        api_response: Dictionary containing, region, package, arn and requirements.txt data
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DB_NAME"])
    region = event.get("pathParameters").get("region")
    package = event.get("pathParameters").get("package")
    python_version = event.get("pathParameters").get("python_version", "p3.8")

    pk = f"lyr#{region}:{package}:{python_version}"
    sk = "lyrVrsn0#"

    try:
        response = table.get_item(
            Key={"pk": pk, "sk": sk},
            AttributesToGet=["rgn", "pckg", "arn", "rqrmntsTxt", "pckgVrsn"],
        )
        api_response = map_keys([response["Item"]])[0]

    except ClientError as e:
        logger.error(
            {
                "message": response["Error"]["Message"],
                "pk": pk,
                "sk": sk,
            }
        )
        api_response = {}
    except KeyError as e:  # no item return
        api_response = {}

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(api_response),
    }
