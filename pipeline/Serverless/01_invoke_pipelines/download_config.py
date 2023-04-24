import requests
import os
import csv
import io
import boto3

from aws_lambda_powertools.logging import Logger

logger = Logger()

configs = {
    "p3.8": "packages_p38.csv",
    "p3.9": "packages_p39.csv",
    "p3.10": "packages_p310.csv",
    "p3.10-arm64": "packages_p310-arm64.csv"
}
region_config_filename = "regions.csv"

branch = "master"


def load_config_into_dynamo(
    config_items: list, python_version: str, config_type: str
) -> dict:
    """
    Args:
        config_items: List of config Items to load
        python_version: Version of python (e.g. p3.8, p3.9)
        config_type: What type of item (e.g. rgns, pckgs) remember the 's'
    Returns: None
    """
    logger.info(
        f"Putting Dynamo Item type: {config_type} for python_version: {python_version}"
    )
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DB_NAME"])
    response = table.put_item(
        Item={
            "pk": f"cnfg#{config_type}",
            "sk": python_version,
            "cnfg": config_items,
        }
    )
    logger.info(response)
    return response


def download_csv_from_github(url: str) -> csv.DictReader:
    logger.info(f"Requesting latest config from {url}")
    response = requests.get(url)

    # Sanity check on csv file
    file_as_string = response.content.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(file_as_string))

    return csv_reader


@logger.inject_lambda_context
def download_config_from_github(event, context):
    """
    Download Config from GitHub
    """
    github_repo = os.environ["GITHUB_REPO"]
    repo_name_branch = f"{github_repo.split(':')[1].split('.')[0]}/{branch}"
    base_url = f"https://raw.githubusercontent.com/{repo_name_branch}/pipeline/config"

    for python_version in configs.keys():
        url = f"{base_url}/{configs[python_version]}"
        csv_reader = download_csv_from_github(url)
        packages = [line["Package_Name"] for line in csv_reader]
        logger.info(f"Found {len(packages)} packages")
        load_config_into_dynamo(
            config_items=packages, python_version=python_version, config_type="pckgs"
        )

        url = f"{base_url}/{region_config_filename}"
        csv_reader = download_csv_from_github(url)
        regions = [line["Code"] for line in csv_reader]
        logger.info(f"Found {len(regions)} regions")
        load_config_into_dynamo(
            config_items=regions, python_version=python_version, config_type="rgns"
        )

    return None
