import os
import logging
import boto3
import datetime

from boto3.dynamodb.conditions import Key

from get_config import get_packages


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def delete_old_layer_versions(table, client, region, package, max_days_older):

    """
    Loops through all layer versions found in DynamoDB and deletes layer version if it's <maximum_days_older> than
    latest layer version.

    The latest layer version is always kept

    Because lambda functions are created at a maximum rate of once per day, a maximum of 14 layers can exists at one
    time.
    """

    # Sort key is lambda version -- by default takes the latest if ScanIndexForward is false
    response = table.query(KeyConditionExpression=Key("deployed_region-package").eq(f"{region}.{package}"),
                           ScanIndexForward=False)

    latest_created_date = datetime.datetime.strptime(response['Items'][0]['created_date'][:10], "%Y-%m-%d")

    for item in response['Items'][1:]:  # ensure at least one lambda is left
        created_date = datetime.datetime.strptime(item['created_date'][:10], "%Y-%m-%d")

        delta = latest_created_date - created_date
        if delta.days > max_days_older:
            logger.info(f"{item['layer_version_arn']} is {delta.days} old, deleting...")
            layer_arn = ":".join(item['layer_version_arn'].split(':')[:-1])
            delete_lambda_response = client.delete_layer_version(LayerName=layer_arn,
                                                                VersionNumber=item['layer_version'])
            logger.info(f"Deleting item {region}.{package} with layer_version {item['layer_version']} from DynamoDB")
            delete_item_response = table.delete_item(Key={"deployed_region-package": f"{region}.{package}",
                                                           "layer_version": item['layer_version']})

    return


def main(event, context):

    region = event['region']
    max_days_older = os.environ['MAX_DAYS_OLDER']
    packages = get_packages()

    client = boto3.client('lambda', region_name=region)

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['LAYERS_DB'])

    for package in packages:
        delete_old_layer_versions(client=client,
                                  table=table,
                                  region=region,
                                  package=package,
                                  max_days_older=max_days_older)
    return {"status": "done"}