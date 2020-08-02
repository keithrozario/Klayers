import os
from boto3.dynamodb.conditions import Key

import boto3

from aws_lambda_powertools.logging import Logger

logger = Logger()

build_v0 = "bldVrsn0#"
package_prefix = "pckg#"


def query_requirements():
    """
    Args:
    returns:
      items: All the requriements_txt of the latest packages
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DB_NAME"])
    kwargs = {
        "KeyConditionExpression": Key("pk").eq(build_v0),
    }
    items = []

    while True:
        response = table.query(**kwargs)
        items.extend(response["Items"])

        try:
            kwargs["ExclusiveStartKey"] = response["ExclusiveStartKey"]
        except KeyError:
            logger.info({"message": "Reached End of Query", "num_items": len(items)})
            break

    return items


@logger.inject_lambda_context
def main(event, context):

    """
    Gets requirements_txt to publish to packages dir
    """

    bucket = os.environ["BUCKET_NAME"]
    items = query_requirements()

    for item in items:

        package_name = item["sk"][len(package_prefix) :]
        requirements_txt = item["rqrmntsTxt"]
        key = f"packages/{package_name}/requirements.txt"

        logger.info(
            {
                "message": "Uploading to bucket",
                "package": package_name,
                "requirements_txt": requirements_txt,
                "bucket": bucket,
            }
        )
        client = boto3.client("s3")
        client.put_object(
            Body=requirements_txt.encode("utf-8"), Bucket=bucket, Key=key,
        )

    return {
        "status": "Done",
        "num_packages": len(items),
    }
