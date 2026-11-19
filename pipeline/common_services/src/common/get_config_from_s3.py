import csv
import json
import os
from pathlib import Path

import boto3


def download_packages_from_s3(python_version: str) -> list[str]:
    s3 = boto3.client("s3")
    bucket = os.environ["CONFIG_BUCKET"]
    config_file_name = "config.json"
    local_config = Path(f"/tmp/{config_file_name}")
    s3.download_file(bucket, config_file_name, str(local_config))

    with open(local_config) as config_file:
        config_data = json.loads(config_file.read())
        python_package_file_name = config_data[python_version]["packages_file"]

    local_packages = Path(f"/tmp/{python_package_file_name}")
    s3.download_file(bucket, python_package_file_name, str(local_packages))

    with open(local_packages) as python_package_file:
        csv_reader = csv.DictReader(python_package_file)
        packages_in_csv = [line["Package_Name"] for line in csv_reader]

    return packages_in_csv


def download_regions_from_s3() -> list[str]:
    s3 = boto3.client("s3")
    bucket = os.environ["CONFIG_BUCKET"]
    region_file_name = "regions.csv"
    local_regions = Path(f"/tmp/{region_file_name}")
    s3.download_file(bucket, region_file_name, str(local_regions))

    with open(local_regions) as region_file:
        csv_reader = csv.DictReader(region_file)
        regions_in_csv = [line["Code"] for line in csv_reader]

    return regions_in_csv


def download_python_versions_from_s3() -> list[str]:
    s3 = boto3.client("s3")
    bucket = os.environ["CONFIG_BUCKET"]
    config_file_name = "config.json"
    local_config = Path(f"/tmp/{config_file_name}")
    s3.download_file(bucket, config_file_name, str(local_config))

    with open(local_config) as config_file:
        config = json.loads(config_file.read())

    python_versions: list[str] = config["python_versions"]
    return python_versions
