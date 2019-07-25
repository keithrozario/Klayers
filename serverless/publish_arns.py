import os
import json
import logging
import decimal
from boto3.dynamodb.conditions import Key

import boto3

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


def main(event, context):

    """
    Gets layer arns for each region and publish to S3
    """

    region = event['region']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['LAYERS_DB'])
    bucket = os.environ['BUCKET_NAME']

    response = table.query(IndexName="LayersPerRegion",
                           Select="SPECIFIC_ATTRIBUTES",
                           ProjectionExpression="#region, layer_version_arn, package, package_version",
                           KeyConditionExpression=Key('region').eq(region),
                           ExpressionAttributeNames={"#region": "region"})

    logger.info(f"Found {len(response['Items'])}")
    arns = json.dumps(response['Items'], cls=DecimalEncoder)

    logger.info(f"Uploading to S3 Bucket")
    client = boto3.client('s3')
    client.put_object(Body=arns.encode('utf-8'),
                      Bucket=bucket,
                      Key=f'arns/{region}.json')

    return len(response['Items'])
