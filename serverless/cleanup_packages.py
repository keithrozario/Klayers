import os
import logging
import boto3

from boto3.dynamodb.conditions import Key

from get_config import get_packages


logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['LAYERS_DB'])


def list_layer_version_arns(client, layer_name):

    response = client.list_layer_version(LayerName=f"{layer_name}")
    deployed_layer_version_arns = [LayerVersion['LayerVersionArn'] for LayerVersion in response['LayerVersions']]

    return deployed_layer_version_arns


def delete_old_layer_versions(client, table, region, package, prefix):

    """
    Loops through all layer versions found in DynamoDB and deletes layer version if it's <maximum_days_older> than
    latest layer version.

    The latest layer version is always kept

    Because lambda functions are created at a maximum rate of once per day, a maximum of 14 layers can exists at one
    time.
    """

    deleted_arns = []
    layer_name = f"{prefix}{package}"

    # Get deployed layer versions
    deployed_layer_version_arns = list_layer_version_arns(client=client,
                                                          layer_name=layer_name)

    # Get Live Layer versions (they automatically delete if they're old)
    response = table.query(KeyConditionExpression=Key("deployed_region-package").eq(f"{region}.{package}"),
                           ScanIndexForward=False)
    live_layer_version_arns = [item['layer_version_arn'] for item in response['Items']]

    # Delete layer versions
    for layer_version_arn in deployed_layer_version_arns:
        if layer_version_arn not in live_layer_version_arns:
            logger.info(f"Found dead layer version {layer_version_arn}...deleting")
            layer_version = layer_version_arn.split(":")[-1]
            client.delete_layer_version(
                LayerName=layer_name,
                VersionNumber=layer_version
            )
            deleted_arns.append(layer_version_arn)
        else:
            pass

    return deleted_arns


def main(event, context):

    region = event['region']
    packages = get_packages()
    lambda_prefix = os.environ['LAMBDA_PREFIX']

    client = boto3.client('lambda', region_name=region)
    deleted_arns = []

    for package in packages:
        arns = delete_old_layer_versions(client=client,
                                         table=table,
                                         region=region,
                                         package=package,
                                         prefix=lambda_prefix)
        deleted_arns.extend(arns)

    return {"deleted_arns": deleted_arns}