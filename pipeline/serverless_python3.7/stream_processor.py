import logging
import json


import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main(event, context):

    records = event.get('Records', [])
    logger.info(f"{len(records)} to process")

    for record in records:
        logger.info(f"Removal of f{json.dumps(record.get('dynamodb').get('Keys'))}")
        if record['eventName'] == 'REMOVE':
            layer_version_arn = remove(record)

        else:
            logger.info(f"No processing required for event type: {record['eventName']}")

    return {"status": "Done"}


def remove(record):

    try:

        layer_version_arn = record['dynamodb']['OldImage']['layer_version_arn']['S']
        logger.info(f"Deleting: {layer_version_arn}")

        arn_elements = layer_version_arn.split(":")
        region = arn_elements[3]
        layer_name = arn_elements[6]
        layer_version = int(arn_elements[7])
    except KeyError:
        logger.error("Unexpected error trying to retrieve layer_Version_arn")
        return

    client = boto3.client('lambda', region_name=region)

    try:
        client.delete_layer_version(
            LayerName=layer_name,
            VersionNumber=layer_version
        )
        logger.info(f"Successfully deleted {layer_version_arn}")
    except AttributeError:
        logger.error(f"Unable to delete layer {layer_version_arn}")
    except ClientError as e:
        logger.error(f"{e.response['Error']['Code'] : {e.response['Error']['Message']}}")

    return layer_version_arn
