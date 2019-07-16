import os
import logging
import boto3

from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main(event, context):

    package = event['package']
    version = event['version']
    regions = event['regions']
    req_hash = event['req_hash']
    license_info = event['license_info']

    layer_name = f"{os.environ['LAMBDA_PREFIX']}{package}"
    package_artifact = f"{package}.zip"

    logger.info(f"Downloading {package_artifact} from {os.environ['BUCKET_NAME']}")
    s3 = boto3.resource('s3')
    s3.meta.client.download_file(os.environ['BUCKET_NAME'],
                                 package_artifact,
                                 f"/tmp/{package_artifact}")
    with open(f"/tmp/{package_artifact}", 'rb') as zip_file:
        zip_binary = zip_file.read()
    logger.info(f"Package {package_artifact} downloaded")

    logger.info(f"Deploying new version of {layer_name}, {package}=={version}, requirements hash: {req_hash}")

    for region in regions:
        logger.info(f"Deploying {layer_name} to {region}")
        lambda_client = boto3.client('lambda', region_name=region)
        response = lambda_client.publish_layer_version(LayerName=layer_name,
                                                       Description=f"{package}=={version} | {req_hash}",
                                                       Content={'ZipFile': zip_binary},
                                                       CompatibleRuntimes=['python3.6', 'python3.7'],
                                                       LicenseInfo=license_info)

        layer_version_arn = response['LayerVersionArn']
        layer_version_created_date = response['CreatedDate']
        logger.info(f"Uploaded new version with arn: {layer_version_arn} at {layer_version_created_date}")

        layer_version = int(layer_version_arn.split(":")[-1])
        logger.info(f"Layer version for {layer_version_arn} is {layer_version}")

        dynamodb_client = boto3.client('dynamodb')
        try:
            dynamodb_client.put_item(TableName=os.environ['LAYERS_DB'],
                                     Item={'region': {'S': region},
                                           'region-package': {'S': f"{region}-{package}"},
                                           'package': {'S': package},
                                           'package_version': {'S': f"{str(version)}"},
                                           'requirements_hash': {'S': req_hash},
                                           'createdDate': {'S': layer_version_created_date},
                                           'layer_version': {'N': str(layer_version)},
                                           'layer_version_arn': {'S': str(layer_version_arn)}})
            logger.info(f"Successfully written {package}:{layer_version} status to DB with hash: {req_hash}")
        except ClientError as e:
            logger.info("Unexpected error Writing to DB: {}".format(e.response['Error']['Code']))

        response = lambda_client.add_layer_version_permission(LayerName=layer_name,
                                                              VersionNumber=layer_version,
                                                              StatementId='make_public',
                                                              Action='lambda:GetLayerVersion',
                                                              Principal='*')
        logger.info(response['Statement'])

    return 0
