import json
import os

import boto3
from aws_lambda_powertools.logging import Logger
from botocore.exceptions import ClientError

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
    path_params = event.get("pathParameters") or {}
    region = path_params.get("region")
    package = path_params.get("package")
    python_version = path_params.get("python_version", "p3.8")

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
                "message": e.response.get("Error", {}).get("Message", str(e)),
                "pk": pk,
                "sk": sk,
            }
        )
        api_response = {}
    except KeyError:  # no item return
        api_response = {}

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(api_response),
    }
