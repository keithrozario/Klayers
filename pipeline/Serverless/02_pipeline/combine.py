import os
import shutil
from zipfile import ZipFile

import boto3

from aws_lambda_powertools.logging import Logger

logger = Logger()

s3 = boto3.client("s3")


@logger.inject_lambda_context
def main(event, context):
    """
    Combines multiple packages into a single zip file
    Function downloads layer for packages from S3, unzips them, and combines them all into a single zip
    Uploads zip into S3 with a new name
    Does **not** deploy, Does **not** write to Dynamo
    """

    packages = event["packages"]
    version = "1.0-man"
    build_flag = False
    name = combined_name(packages)
    python_version = event["python_version"]
    zip_file_S3key = f"{python_version}/{name}.zip"
    requirements_hash = "n.a custom build"
    license_info = "Refer for individual package"
    force_deploy = True

    archive_path = combine_packages(
        packages=packages, python_version=python_version, combined_name=name
    )
    upload_to_s3(archive_path=archive_path, s3_location=zip_file_S3key)

    return {
        "zip_file_S3key": zip_file_S3key,
        "package": name,
        "version": version,
        "requirements_hash": requirements_hash,
        "license_info": license_info,
        "build_flag": build_flag,
        "force_deploy": force_deploy,
        "python_version": python_version,
    }


def combined_name(packages: list[str]) -> str:
    """
    Args:
        packages: List of strings of packages to combine
    returns:
        combined_name: String of combined package name with dash in between
        Eg: custom-pandas-tabulate-...

    Example:
        packages = ["pandas", "tabulate"]
        combined_name = "custom-pandas-tabulate-..."

    Example:
        packages = ["pandas", "numpy", "tabulate", "scipy"]
        combined_name = "custom-pandas-numpy-tabulate-scipy-...
    """
    combined_name = "custom"
    for name in packages:
        combined_name = combined_name + "-" + name

    logger.info(f"New name: {combined_name}")
    return combined_name


def combine_packages(
    packages: list[str], python_version: str, combined_name: str
) -> None:
    """
    Args:
        packages: List of strings of packages to combine
        python_version: String of python version
        combined_name: Name of combined package
    returns:
        combined_name: combined file name to upload
    """

    archive_path = f"/tmp/{combined_name}.zip"

    for package in packages:
        s3_key = f"{python_version}/{package}.zip"
        download_path = f"/tmp/{package}.zip"
        s3.download_file(os.environ["BUCKET_NAME"], s3_key, download_path)
        logger.info(f"Download {s3_key} to {download_path}")
        # Unzip file
        with ZipFile(download_path, "r") as zip_object:
            zip_object.extractall("/tmp")

    result = shutil.make_archive(
        base_name=archive_path.split(".")[0],  # remove the .zip
        format="zip",
        base_dir="python",
        root_dir="/tmp",
    )

    return archive_path


def upload_to_s3(archive_path: str, s3_location: str):
    """
    Args:
        archive_path: Location of zip file to be uploaded to S3 bucket
        combined_name: Name of combined package
    returns:
        uploaded_file_name: Name of file in S3 bucket
    """
    bucket_name = os.environ["BUCKET_NAME"]

    logger.info(
        f"Uploading {archive_path} with name {s3_location} to S3 bucket {bucket_name}"
    )
    s3.upload_file(archive_path, bucket_name, s3_location)

    return None
