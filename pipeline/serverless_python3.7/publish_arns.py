import os
import json
import logging
import decimal
from boto3.dynamodb.conditions import Key

import boto3

import get_config

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def query_versions_table(region, table):
    """
    Args:
      table: DynamoDB table object to query
      region: region to query on
    returns:
      items: items returned from the query
    """

    kwargs = {
        "IndexName": "LayersPerRegion",
        "Select": "SPECIFIC_ATTRIBUTES",
        "ProjectionExpression": "deployed_region, layer_version_arn, package, package_version, time_to_live",
        "KeyConditionExpression": Key('deployed_region').eq(region)
    }
    items = []

    while True:
        response = table.query(**kwargs)
        items.extend(response['Items'])

        try:
            kwargs['ExclusiveStartKey'] = response['ExclusiveStartKey']
        except KeyError:
            logger.info(f"Reached end of query for {region}, Returning {len(items)} items")
            break

    return items


def main(event, context):

    """
    Gets layer arns for each region and publish to S3
    """

    regions = get_config.get_aws_regions()

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['LAYERS_DB'])
    bucket = os.environ['BUCKET_NAME']

    for region in regions:

        items = query_versions_table(table=table,
                                     region=region)
        arns = json.dumps(items, cls=DecimalEncoder, indent=4)

        logger.info(f"Uploading to S3 Bucket")
        client = boto3.client('s3')
        client.put_object(Body=arns.encode('utf-8'),
                          Bucket=bucket,
                          Key=f'arns/{region}.json')

    return {"status": "Done"}
