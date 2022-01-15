import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from aws_lambda_powertools.logging import Logger
from common.dynamodb import DecimalEncoder, map_keys, query_till_end

logger = Logger()


def query_table(region: str, table: str, python_version: str) -> list:
    """
    Args:
      table: DynamoDB table object to query
      region: region to query on
      python_version: version of python (e.g. p3.9, p3.8)
    returns:
      items: items returned from the query
    """

    kwargs = {
        "IndexName": "deployed_in_region_by_python_version",
        "KeyConditionExpression": Key("rgn#PyVrsn").eq(f"{region}:{python_version}") & Key("dplySts").eq("latest"),
        "ProjectionExpression": "pckg, arn, pckgVrsn",
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
    python_version = event.get("pathParameters").get("python_version", "p3.8")
    api_response = query_table(table=table, region=region, python_version=python_version)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(api_response, cls=DecimalEncoder),
    }
