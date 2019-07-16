import json
import os
import logging

import boto3
import requests
from packaging.version import parse
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_latest_deployed_version(region, package):
    """
    Args:
      package: Name of package to be queried
      region: region to query for
    returns:
      last_deployed_version: Last deployed version for that region as packaging.version
    """

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['LAYERS_DB'])

    # Sort key is lambda version -- by default takes the latest if ScanIndexForward is false
    response = table.query(KeyConditionExpression=Key("region-package").eq(f"{region}-{package}"),
                           Limit=1,
                           ScanIndexForward=False)

    if len(response['Items']) > 0:
        last_deployed_version = parse(response['Items'][0]['package_version'])
    else:
        last_deployed_version = False

    return last_deployed_version


def get_latest_release(package):
    """
    Args:
      package: Name of package to be queried
    returns:
      version: Version number of latest release that is **not** a pre-release as packaging.version
    """
    req = requests.get(f"https://pypi.python.org/pypi/{package}/json")
    version = parse('0')
    if req.status_code == requests.codes.ok:
        j = json.loads(req.text)
        releases = j.get('releases', [])
        license = j.get('license', "No-License-in-PyPI")
        for release in releases:
            ver = parse(release)
            if not ver.is_prerelease:
                version = max(version, ver)

    return version, license


def get_aws_regions():

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


def main(event, context):
    """
    Args:
      package: Package to check for
    return:
      needs_building: Boolean indicating if a build is required
      package: Name of package
      regions: List of AWS regions to deploy to
    """

    package = event['package']
    needs_building=False
    build_regions = []
    regions = get_aws_regions()

    latest_version, license_info = get_latest_release(package)
    logger.info(f"Latest version of package:{package} on pypi is {latest_version}")

    for region in regions:
        last_deployed_version = get_latest_deployed_version(region, package)
        logger.info(f"Last Deployed version of package:{package} in {region} is {last_deployed_version}")

        if last_deployed_version:

            if latest_version > last_deployed_version:
                logger.info(f"{region} will be upgraded to {latest_version}")
                needs_building = True
                build_regions.append(region)
            else:
                logger.info(f"{region} already has {last_deployed_version} -- not deploying")

        else:
            logger.info(f"{region} has no version of {package} deployed -- deploying")
            needs_building = True
            build_regions.append(region)

    return {"needs_building": needs_building,
            "version": str(latest_version),
            "package": package,
            "regions": build_regions,
            "license_info": license_info}