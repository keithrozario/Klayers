import os
import json
import csv
import boto3


def download_packages_from_s3(python_version: str) -> list():
    s3 = boto3.client("s3")
    config_file_name = "config.json"
    s3.download_file(
        os.getenv("CONFIG_BUCKET"), config_file_name, f"/tmp/{config_file_name}"
    )
    with open(f"/tmp/{config_file_name}", "r") as config_file:
        python_package_file_name = json.loads(config_file.read())[python_version][
            "packages_file"
        ]

    s3.download_file(
        os.getenv("CONFIG_BUCKET"),
        python_package_file_name,
        f"/tmp/{python_package_file_name}",
    )
    with open(f"/tmp/{python_package_file_name}", "r") as python_package_file:
        csv_reader = csv.DictReader(python_package_file)
        packages_in_csv = [line["Package_Name"] for line in csv_reader]

    return packages_in_csv


def download_regions_from_s3() -> list():
    s3 = boto3.client("s3")
    region_file_name = "regions.csv"
    s3.download_file(
        os.getenv("CONFIG_BUCKET"), region_file_name, f"/tmp/{region_file_name}"
    )
    with open(f"/tmp/{region_file_name}", "r") as region_file:
        csv_reader = csv.DictReader(region_file)
        regions_in_csv = [line["Code"] for line in csv_reader]

    return regions_in_csv
