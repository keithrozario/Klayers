import os
import json
import decimal
import boto3
from boto3.dynamodb.conditions import Key
from aws_lambda_powertools.logging import Logger
from common.dynamodb import DecimalEncoder, map_keys, query_till_end

logger = Logger()


def query_table(table):
    """
    Args:
      table: DynamoDB table object to query
    returns:
      items: items returned from the query
    """

    kwargs = {
        "KeyConditionExpression": Key("pk").eq("bldVrsn0#"),
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
    api_response = query_table(table=table)

    return {
        "statusCode": 200,
        "body": json.dumps(api_response, cls=DecimalEncoder),
    }
