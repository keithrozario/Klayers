import logging
import json
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools.logging import Logger
logger = Logger()


@logger.inject_lambda_context
def main(event, context):

    records = event.get('Records', [])
    logger.info({
        "message": "Verifying records",
        "record_count": len(records),
        })

    for record in records:

        logger.debug({
            "message": "Checking record",
            "keys": json.dumps(record.get('dynamodb').get('Keys'))})
        if record['eventName'] == 'REMOVE':
            remove(record)
        else:
            logger.debug({"message": "Not a deletion record"})

    return {"status": "Done"}


def remove(record):
    """
    Deletes lambda_layer_arn from account.
    record: record from DynamoDB Table
    """

    try:
        old_image = record['dynamodb']['OldImage']
        layer_version_arn = old_image['arn']['S']
        deploy_status = old_image['dplySts']['S']  # to see if it's a arn record
        logger.info({
            "message": "Deleting",
            "layer_arn": layer_version_arn,
            "deploy_status": deploy_status,
        })
        arn_elements = layer_version_arn.split(":")
        region = arn_elements[3]
        layer_name = arn_elements[6]
        layer_version = int(arn_elements[7])
    except KeyError:
        logger.error({"message": "Not a arn element"})
        return 
    except IndexError:
        logger.error("Unexpected Error")
        return

    client = boto3.client('lambda', region_name=region)

    try:
        insert_expired_record(old_image)
        client.delete_layer_version(
            LayerName=layer_name,
            VersionNumber=layer_version
        )
    except AttributeError:
        logger.error({"message": "Unable to delete layer", "arn": layer_version_arn})
    except ClientError as e:
        logger.error(f"{e.response['Error']['Code'] : {e.response['Error']['Message']}}")

    return

def insert_expired_record(old_image):
    """
    Inserts a expired record back to DB, removing the dplySts, and entering a deleted date
    """

    if 'dplySts' in old_image.keys():
        del old_image['dplySts']
    else:
        logger.error("No Deploy status found in entry...")
        return

    old_image['dltdDt'] = {'S': datetime.utcnow().isoformat()}
    del old_image['exDt']

    client = boto3.client('dynamodb')
    table_name = os.environ['DB_NAME']

    client.put_item(
        TableName=table_name,
        Item=old_image,
    )

    return 