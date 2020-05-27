import os
import json
import logging
import decimal
import csv
import time
from datetime import datetime

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


def convert_to_csv(items):
    """
    Args:
      items: all arns in a region from the DynamoDB query as a list
    returns:
      csv_body: body of the csv file to write out
    """

    fieldnames = ['Package','Package Version','Status','Expiry Date','Arn']

    # sort by package, and then created date (oldest to newest)
    sorted_items = sorted(items, key=lambda i: (i['pckg'].lower(), i['crtdDt']))

    with open('/tmp/packages.csv', 'w', newline='') as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in sorted_items:

            # convert datetime to human readable
            try:
                if item['exDt']:
                    item['exDt'] = datetime.utcfromtimestamp(item['exDt']).isoformat()
            except KeyError:
                item['exDt'] = ""
            
            csv_item = {
                "Package": item['pckg'],
                "Package Version": item['pckgVrsn'],
                "Arn": item['arn'],
                "Status": item['dplySts'],
                "Expiry Date": item['exDt'],
            }
            writer.writerow(csv_item)

    with open('/tmp/packages.csv', 'r') as csvfile:
        csv_text = csvfile.read()

    return csv_text


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
        "KeyConditionExpression": Key('rgn').eq(region),
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
    table = dynamodb.Table(os.environ['DB_NAME'])
    bucket = os.environ['BUCKET_NAME']
    region_deploy = dict()

    for region in regions:

        items = query_table(table=table,
                                     region=region)
        arns = convert_to_csv(items)
        region_deploy[region] = len(items)

        logger.info(f"Uploading to S3 Bucket")
        client = boto3.client('s3')
        client.put_object(Body=arns.encode('utf-8'),
                          Bucket=bucket,
                          Key=f'arns/{region}.csv')

    return {"arn_count": region_deploy}
