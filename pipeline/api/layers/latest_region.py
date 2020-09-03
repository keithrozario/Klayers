import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from aws_lambda_powertools.logging import Logger
from common.dynamodb import DecimalEncoder, map_keys, query_till_end

logger = Logger()


def query_table(region, table):
    """
    Args:
      table: DynamoDB table object to query
      region: region to query on
    returns:
      items: items returned from the query
    """

    kwargs = {
        "IndexName": "deployed_in_region",
        "KeyConditionExpression": Key("rgn").eq(region) & Key("dplySts").eq("latest"),
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
    api_response = query_table(table=table, region=region)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type" : "application/json"
        },
        "body": json.dumps(api_response, cls=DecimalEncoder),
    }
