import os
import json

import boto3
from boto3.dynamodb.conditions import Key

from aws_lambda_powertools.logging import Logger

logger = Logger()

from common.dynamodb import DecimalEncoder, map_keys, query_till_end


def query_table(region, table, pk):
    """
    Args:
      table: DynamoDB table object to query
      region: region to query on
    returns:
      items: items returned from the query
    """

    kwargs = {
        "KeyConditionExpression": Key("pk").eq(pk),
        "ProjectionExpression": "arn, pckgVrsn, dplySts, rqrmntsTxt, exDt",
        "FilterExpression": "attribute_exists(dplySts)",  # don't get latest version
    }
    items = query_till_end(table=table, kwargs=kwargs)

    return map_keys(items)


@logger.inject_lambda_context
def main(event, context):
    """
    Gets layer arns for each region and publish to S3
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DB_NAME"])
    region = event.get("pathParameters").get("region")
    package = event.get("pathParameters").get("package")
    python_version = event.get("pathParameters").get("python_version", "p3.8")
    pk = f"lyr#{region}:{package}:{python_version}"
    api_response = query_table(table=table, region=region, pk=pk)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(api_response, cls=DecimalEncoder),
    }
