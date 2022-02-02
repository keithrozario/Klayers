import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from aws_lambda_powertools.logging import Logger
from common.dynamodb import DecimalEncoder, map_keys, query_till_end

logger = Logger()


def query_table(table, python_version: str):
    """
    Args:
      table: DynamoDB table object to query
      python_version: Version of python (e.g. p3.8, p3.9)
    returns:
      items: items returned from the query
    """

    kwargs = {
        "KeyConditionExpression": Key("pk").eq(f"bldVrsn0#{python_version}"),
        "ProjectionExpression": "crtdDt, pckg, pckgVrsn, rqrmntsTxt",
    }
    items = query_till_end(table=table, kwargs=kwargs)

    return map_keys(items)


@logger.inject_lambda_context
def main(event, context):
    """
    Gets latest build for all packages
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DB_NAME"])
    python_version = event.get("pathParameters", {}).get("python_version", "p3.8")
    api_response = query_table(table=table, python_version=python_version)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(api_response, cls=DecimalEncoder),
    }
