import os
from datetime import datetime

import boto3
from aws_lambda_powertools.logging import Logger

logger = Logger()


@logger.inject_lambda_context
def main(event, context):
    record = event["detail"]["record"]
    logger.debug({"record": record})
    remove(record)
    return


def remove(record):
    """
    Deletes lambda_layer_arn from account.
    record: record from DynamoDB Table
    """

    old_image = record["dynamodb"]["OldImage"]
    layer_version_arn = old_image["arn"]["S"]
    deploy_status = old_image["dplySts"][
        "S"
    ]  # to see if it's a arn record, Key error otherwise
    logger.info(
        {
            "message": "Deleting",
            "layer_arn": layer_version_arn,
            "deploy_status": deploy_status,
        }
    )
    arn_elements = layer_version_arn.split(":")
    region = arn_elements[3]
    layer_name = arn_elements[6]
    layer_version = int(arn_elements[7])

    client = boto3.client("lambda", region_name=region)

    insert_expired_record(old_image)
    client.delete_layer_version(LayerName=layer_name, VersionNumber=layer_version)
    logger.info(
        {"message": "Deleted Layer", "arn": layer_version_arn,}
    )

    return


def insert_expired_record(old_image):
    """
    Inserts a expired record back to DB, removing the dplySts, and entering a deleted date
    """

    del old_image["dplySts"]
    old_image["dltdDt"] = {"S": datetime.utcnow().isoformat()}

    try:
        del old_image["exDt"]
    except KeyError:
        logger.warning("Image doesn't have exDt entry")

    client = boto3.client("dynamodb")
    table_name = os.environ["DB_NAME"]

    client.put_item(
        TableName=table_name, Item=old_image,
    )
    logger.info(
        {"message": "Inserted Deleted Layer into table", "record": old_image,}
    )
    return
