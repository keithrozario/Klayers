import os
import json
import decimal
import boto3
from boto3.dynamodb.conditions import Key
from aws_lambda_powertools.logging import Logger

logger = Logger()

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

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
        "ProjectionExpression": "pckg, arn, pckgVrsn"
    }
    items = []

    while True:
        response = table.query(**kwargs)
        items.extend(response["Items"])

        try:
            kwargs["ExclusiveStartKey"] = response["ExclusiveStartKey"]
        except KeyError:
            logger.info({
                "region": region,
                "num_items": len(items),
                "message": "Completed Query for objects in region"
            }
            )
            break

    return items

@logger.inject_lambda_context
def main(event, context):
    """
    Gets layer arns for each region and publish to S3
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DB_NAME"])
    region = event.get('pathParameters').get('region')
    api_response = query_table(table=table, region=region)

    return {
        "statusCode": 200,
        "body": json.dumps(api_response, cls=DecimalEncoder),
    }
