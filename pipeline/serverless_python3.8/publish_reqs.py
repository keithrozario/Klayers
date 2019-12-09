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


def main(event, context):

    """
    Gets layer arns for each region and publish to S3
    """

    packages = get_config.get_packages()

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['REQS_DB'])
    bucket = os.environ['BUCKET_NAME']

    for package in packages:

        response = table.query(IndexName="packageHistory",
                               Select="SPECIFIC_ATTRIBUTES",
                               ProjectionExpression="package, requirements",
                               KeyConditionExpression=Key('package').eq(package),
                               Limit=1,
                               ScanIndexForward=False)  # takes the package with the latest created date

        logger.info(f"Found {len(response['Items'])} entries for {package}")

        try:
            requirements_txt = response['Items'][0]['requirements']
            logger.info(f"Requirements.txt for {package} is {requirements_txt}")
            logger.info(f"Uploading to S3 Bucket")
            client = boto3.client('s3')
            client.put_object(Body=requirements_txt.encode('utf-8'),
                          Bucket=bucket,
                          Key=f'packages/{package}/requirements.txt')
        except IndexError:
            logger.error(f"No records found for {package}")

    return {"status": "Done"}
