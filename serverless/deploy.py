import os
import logging
import boto3

from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main(event, context):

    package = event['package']
    version = event['version']
    region = event['region']
    req_hash = event.get('req_hash', 'null')
    license = event.get('license')

    layer_name = f"{os.environ['lambda_prefix']}-{package}"

    s3 = boto3.resource('s3')
    s3.meta.client.download_file(os.environ['BUCKET_NAME'],
                                 f"{package}.zip",
                                 f"/tmp/{package}.zip")

    with open(f"/tmp/{package}.zip", 'rb') as zip_file:
        zip_binary = zip_file.read()

    lambda_client = boto3.client('lambda', region_name=region)

    response = lambda_client.publish_layer_version(
        LayerName=layer_name,
        Description=f"{package} |{req_hash}",
        Content={'ZipFile': zip_binary},
        CompatibleRuntimes=['python3.6','python3.7'],
        LicenseInfo=license
    )

    layer_version_arn = response['LayerVersionArn']
    layer_version_created_date = response['CreatedDate']

    layer_version = layer_version_arn.split(":")[-1]

    dynamodb_client = boto3.client('dynamodb')
    try:
        dynamodb_client.put_item(TableName=os.environ['LAYERS_DB'],
                                 Item={'region': {'S': region},
                                       'package-version': {'S': f"{package}-{str(version)}"},
                                       'requirements_hash': {'S': req_hash},
                                       'createdDate': {'S': layer_version_created_date},
                                       'layer_version': {'S': layer_version},
                                       'layer_version_arn': {'S': layer_version_arn}})
        logger.info(f"Successfully written {package}:{version} status to DB with hash: {req_hash}")
    except ClientError as e:
        logger.info("Unexpected error Writing to DB: {}".format(e.response['Error']['Code']))

    response = lambda_client.add_layer_version_permission(LayerName=layer_name,
                                                          VersionNumber=layer_version,
                                                          StatementId='make_public',
                                                          Action='lambda:GetLayerVersion',
                                                          Principal='*')
    logger.info(response['Statement'])
