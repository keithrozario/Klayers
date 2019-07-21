import boto3
import os
from boto3.dynamodb.conditions import Key
from packaging.version import parse


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
    response = table.query(KeyConditionExpression=Key("region-package").eq(f"{region}-{package}"),
                           Limit=1,
                           ScanIndexForward=False)

    if len(response['Items']) > 0:
        last_deployed_version = parse(response['Items'][0]['package_version'])
        last_deployed_requirements_hash = response['Items'][0]['requirements_hash']
    else:
        last_deployed_version = False
        last_deployed_requirements_hash = "None"

    return last_deployed_version, last_deployed_requirements_hash


def get_aws_regions():
    """
    returns:
        aws_regions : List of all regions to deploy lambdas into
    """

    aws_regions = ['ap-northeast-1', 'ap-northeast-2',
                   'ap-south-1',
                   'ap-southeast-1', 'ap-southeast-2',
                   'ca-central-1',
                   'eu-central-1',
                   'eu-north-1',
                   'eu-west-1', 'eu-west-2', 'eu-west-3',
                   'sa-east-1',
                   'us-east-1', 'us-east-2',
                   'us-west-1', 'us-west-2']

    return aws_regions
