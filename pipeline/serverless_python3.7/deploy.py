import os
import logging
import time

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from packaging.version import parse

import get_config

logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodb_client = boto3.client('dynamodb')
s3 = boto3.resource('s3')


def get_latest_deployed_version(region, package):
    """
    Args:
      package: Name of package to be queried
      region: region to query for
    returns:
      last_deployed_version: Last deployed version for that region as packaging.version object
      last_deployed_reguirements_hash: Hash of the requirements.txt file of the last deployed lambda
    """

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['LAYERS_DB'])

    # Sort key is lambda version -- by default takes the latest if ScanIndexForward is false
    response = table.query(KeyConditionExpression=Key("deployed_region-package").eq(f"{region}.{package}"),
                           Limit=1,
                           ScanIndexForward=False)

    if len(response['Items']) > 0:
        last_deployed_version = parse(response['Items'][0]['package_version'])
        last_deployed_requirements_hash = response['Items'][0]['requirements_hash']
    else:
        last_deployed_version = False
        last_deployed_requirements_hash = "None"

    return last_deployed_version, last_deployed_requirements_hash


def check_latest_deploy(package, region, requirements_hash):
    """
    Args:
        package: Name of package to query
        region: region to query for
        requirements_hash: hash of requirements.txt file
    returns:
        Boolean: False if requirements hash matches latest deployhed version (doesn't need deploying)
                 True if requirements hash does not match latest deployed version (needs deploying)
    """
    last_deployed_version, last_deployed_requirements_hash = get_latest_deployed_version(region=region,
                                                                                         package=package)

    if requirements_hash == last_deployed_requirements_hash:
        return False

    return True


def main(event, context):

    regions = get_config.get_aws_regions()

    package = event['package']
    version = event['version']
    build_flag = event['build_flag']
    package_artifact = event['zip_file']
    requirements_hash = event['requirements_hash']
    license_info = event['license_info']

    deployed_flag = False

    layer_name = f"{os.environ['LAMBDA_PREFIX']}{package}"
    logger.info(f"Downloading {package_artifact} from {os.environ['BUCKET_NAME']}")
    s3.meta.client.download_file(os.environ['BUCKET_NAME'],
                                 package_artifact,
                                 f"/tmp/{package_artifact}")
    with open(f"/tmp/{package_artifact}", 'rb') as zip_file:
        zip_binary = zip_file.read()
    logger.info(f"Package {package_artifact} downloaded")

    logger.info(f"Deploying new version of {layer_name}, {package}=={version}, requirements hash: {requirements_hash}")
    for region in regions:

        if check_latest_deploy(package=package,
                               region=region,
                               requirements_hash=requirements_hash):

            # Publish Layer Version
            logger.info(f"Deploying {layer_name} to {region}")
            lambda_client = boto3.client('lambda', region_name=region)
            response = lambda_client.publish_layer_version(LayerName=layer_name,
                                                           Description=f"{package}=={version} | {requirements_hash}",
                                                           Content={'ZipFile': zip_binary},
                                                           CompatibleRuntimes=['python3.6', 'python3.7'],
                                                           LicenseInfo=license_info)

            layer_version_arn = response['LayerVersionArn']
            layer_version_created_date = response['CreatedDate']
            logger.info(f"Uploaded new version with arn: {layer_version_arn} at {layer_version_created_date}")

            layer_version = int(layer_version_arn.split(":")[-1])
            logger.info(f"Layer version for {layer_version_arn} is {layer_version}")

            try:
                dynamodb_client.put_item(TableName=os.environ['LAYERS_DB'],
                                         Item={'deployed_region': {'S': region},
                                               'deployed_region-package': {'S': f"{region}.{package}"},
                                               'package': {'S': package},
                                               'package_version': {'S': f"{str(version)}"},
                                               'requirements_hash': {'S': requirements_hash},
                                               'created_date': {'S': layer_version_created_date},
                                               'layer_version': {'N': str(layer_version)},
                                               'layer_version_arn': {'S': str(layer_version_arn)}})
                logger.info(
                    f"Successfully written {package}:{layer_version} status to DB with hash: {requirements_hash}")

                if layer_version > 1:
                    ttl_value = int(time.time() + 24*3600*30)
                    dynamodb_client.update_item(TableName=os.environ['LAYERS_DB'],
                                                Key={'deployed_region-package': {'S': f"{region}.{package}"},
                                                     'layer_version': {'N': str(layer_version-1)}},
                                                UpdateExpression='SET time_to_live = :val1',
                                                ExpressionAttributeValues={':val1': {'N': str(ttl_value)}})
                    logger.info(
                        f"Successfully added TTL for 30 days to {region}.{package} version {layer_version-1}")
                else:
                    logger.info(
                        f"No previous version for {region}.{package} found, bypassing delete")

            except ClientError as e:
                logger.error("Unexpected error Writing to DB: {}".format(e.response['Error']['Code']))

            response = lambda_client.add_layer_version_permission(LayerName=layer_name,
                                                                  VersionNumber=layer_version,
                                                                  StatementId='make_public',
                                                                  Action='lambda:GetLayerVersion',
                                                                  Principal='*')
            logger.info(response['Statement'])
            deployed_flag = True

        else:
            logger.info(f"{region} already has latest version installed...")

    return {"deployed_flag": deployed_flag,
            "build_flag": build_flag,
            "package": package,
            "version": version,
            "requirements_hash": requirements_hash}
