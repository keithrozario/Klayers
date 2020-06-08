import os
import logging
import time
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from packaging.version import parse

from aws_lambda_powertools.logging import Logger
logger = Logger()

import get_config


def check_regions_to_deploy(package, requirements_hash, regions):
    """
    Args:
        package: Name of package to deploy
        requirements_hash: Hash of requirements.txt file
        regions: Total regions configured to deployed
    return:
        regions_to_deploy(list): Regions where latest package doesn't match requirements_hash provided
    """
    table_name = os.environ['DB_NAME']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    response = table.query(
        IndexName='package_global',
        KeyConditionExpression=Key('pckg').eq(package) & Key('dplySts').eq('latest')
    )

    # check if there are any region in regions that aren't deployed
    regions_deployed = [item['rgn'] for item in response['Items']]
    regions_to_deploy = [region for region in regions if region not in regions_deployed]
    logger.info({
        "message": f"Deploying to {len(regions_to_deploy)} new regions",
        "new_regions": regions_to_deploy,
        "regions_deployed": regions_deployed,
    })

    # for all deployed regions, check if it has the latest version
    for item in response['Items']:
        if item['rqrmntsHsh'] != requirements_hash:
            if item['rgn'] in regions:
                regions_to_deploy.append(item['rgn'])

    # deduplicate 
    regions_to_deploy = list(set(regions_to_deploy))
    
    logger.info({
        "regions_to_deploy": regions_to_deploy
    })

    return regions_to_deploy


def download_artifact(package_artifact):
    """
    Downloads s3://bucket_name/package_artifact to /tmp directory
    """

    bucket_name = os.environ['BUCKET_NAME']
    s3 = boto3.resource('s3')

    s3.meta.client.download_file(bucket_name,
                                 package_artifact,
                                 f"/tmp/{package_artifact}")
    with open(f"/tmp/{package_artifact}", 'rb') as zip_file:
        zip_binary = zip_file.read()
    logger.info(f"Package {package_artifact} downloaded")
    
    return zip_binary

def get_requirements_txt(package):
    """
    Args:
        package: Name of package to query for
    return:
        requirements_txt (str): Requirements.txt of the package, or "null" ot not present
    """

    build_v0 = 'bldVrsn0#'
    sk = f"pckg#{package}"

    client = boto3.client('dynamodb')
    table_name = os.environ['DB_NAME']
    response = client.get_item(
        TableName=table_name,
        Key={'pk': {'S': build_v0}, 'sk': {'S': sk}},
    )
    logger.info({
        "query_requirements": response 
    })
    requirements_txt = response.get('Item', {}).get('rqrmntsTxt', {}).get('S', "null")

    return requirements_txt

@logger.inject_lambda_context
def main(event, context):

    regions = get_config.get_aws_regions()

    package = event['package']
    version = event['version']
    build_flag = event['build_flag']
    package_artifact = event['zip_file']
    requirements_hash = event['requirements_hash']
    license_info = event['license_info']
    table_name = os.environ['DB_NAME']
    expiry_days = int(os.environ['EXPIRY_DAYS'])

    dynamo_client = boto3.client('dynamodb')
    deployed_flag = False

    # Check if need to deploy
    regions_to_deploy = check_regions_to_deploy(package, requirements_hash, regions)
    if len(regions_to_deploy) == 0:
        logger.info({"message": "No new regions to deploy to, terminating!"})
        return {"deployed_flag": deployed_flag,
                "build_flag": build_flag,
                "package": package,
                "version": version,
                "requirements_hash": requirements_hash}
    logger.info({"message": "Regions to deploy", "regions_to_deploy": regions_to_deploy})

    # Download Lambda Artifact
    layer_name = f"{os.environ['LAMBDA_PREFIX']}{package}"
    zip_binary = download_artifact(package_artifact)

    # Get requirements txt
    requirements_txt = get_requirements_txt(package)

    for region in regions_to_deploy:

        # Publish Layer Version
        logger.info({"message": "Deploying", "region": region, "package": package})
        lambda_client = boto3.client('lambda', region_name=region)
        response = lambda_client.publish_layer_version(
            LayerName=layer_name,
            Description=f"{package}=={version} | {requirements_hash}",
            Content={'ZipFile': zip_binary},
            CompatibleRuntimes=['python3.6', 'python3.7', 'python3.8'],
            LicenseInfo=license_info
        )
        layer_version_arn = response['LayerVersionArn']
        layer_version_created_date = datetime.utcnow().isoformat()
        layer_version = int(layer_version_arn.split(":")[-1])

        # Make Layer Publicly accessible
        logger.info({"message": "Making Public", "region": region, "package": package, "arn": layer_version_arn, "created_date": layer_version_created_date})
        response = lambda_client.add_layer_version_permission(
            LayerName=layer_name,
            VersionNumber=layer_version,
            StatementId='make_public',
            Action='lambda:GetLayerVersion',
            Principal='*'
        )
        
        # Insert new entry into DynamoDB
        logger.info({"message": "Inserting to table", "region": region, "package": package, "arn": layer_version_arn})
        
        pk = f"lyr#{region}.{package}"
        sk_v0 = "lyrVrsn0#"
        sk = f"lyrVrsn#v{layer_version}"
        sk_previous = f"lyrVrsn#v{layer_version-1}"

        response = dynamo_client.transact_write_items(
        TransactItems=[
            {
                'Update': {
                    'TableName': table_name,
                    'Key': {
                        'pk': {'S': pk},
                        'sk': {'S': sk_v0},
                    },
                    'UpdateExpression':
                        "set "
                        "rqrmntsTxt = :rqrmntsTxt, "
                        "pckgVrsn = :pckgVrsn, "
                        "rqrmntsHsh = :rqrmntsHsh,"
                        "arn = :arn,"
                        "crtdDt = :crtdDt,"
                        "lyrVrsn = :lyrVrsn",
                    "ExpressionAttributeValues": {
                        ':rqrmntsTxt': {'S': requirements_txt},
                        ':crtdDt': {'S': layer_version_created_date},
                        ':pckgVrsn': {'S': version},
                        ':rqrmntsHsh': {'S': requirements_hash},
                        ':arn': {'S': layer_version_arn},
                        ':lyrVrsn': {'N': str(layer_version)},
                    },
                    # Allow update only if
                    # Current lyrVrsn is less than updated value
                    # or lyrVrsn doesn't exists
                    "ConditionExpression": "lyrVrsn <= :lyrVrsn OR attribute_not_exists(lyrVrsn)"
                }
            },
            {
                'Put': {
                    'TableName': table_name,
                    'Item': {
                        'pk': {'S': pk},
                        'sk': {'S': sk},
                        'pckgVrsn': {'S': version},
                        'crtdDt': {'S': layer_version_created_date},
                        'rqrmntsTxt': {'S': requirements_txt},
                        'rqrmntsHsh': {'S': requirements_hash},
                        'arn': {'S': layer_version_arn},
                        'pckg': {'S': package},
                        'rgn': {'S': region},
                        'dplySts': {'S': 'latest'},
                        'lyrVrsn': {'N': str(layer_version)},
                    }
                }
            }
        ]
        )
        if layer_version > 1:
            logger.info({"message": "Updating Previous Version", "region": region, "package": package, "arn": layer_version_arn})
            try:
                response = dynamo_client.update_item(
                    TableName=table_name,
                    Key={
                        'pk': {'S': pk},
                        'sk': {'S': sk_previous}
                    },
                    UpdateExpression="set "
                    "dplySts = :dplySts, "
                    "exDt = :exDt",
                    ExpressionAttributeValues={
                        ":dplySts": {'S': "deprecated"},
                        ":exDt": {'N': str(int(time.time() + 24*3600*expiry_days))},
                    },
                    ConditionExpression="attribute_exists(sk)"
                )
            except ClientError as e:  
                if e.response['Error']['Code']=='ConditionalCheckFailedException':
                    logger.warning({"message": "Conditional Check failed", "layer_version": layer_version, 'sk': sk_previous})
        deployed_flag = True

    return {
        "deployed_to": regions_to_deploy,
        "deployed_flag": deployed_flag,
        "build_flag": build_flag,
        "package": package,
        "version": version,
        "requirements_hash": requirements_hash
    }
