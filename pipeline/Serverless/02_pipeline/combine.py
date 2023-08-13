import os
import shutil
from zipfile import ZipFile

import boto3

from common.get_config import get_from_common_service
from common.get_compatible import get_compatible_runtimes, get_compatible_architectures

from aws_lambda_powertools.logging import Logger

logger = Logger()

s3 = boto3.client("s3")


@logger.inject_lambda_context
def main(event, context):
    """
    Combines multiple packages into a single zip file
    Function downloads layer for packages from S3, unzips them, and combines them all into a single zip
    Uploads zip into S3 with a new name
    Deploys to all regions
    """

    packages = event["packages"]
    combined_package_name = combined_name(packages)
    python_version = event["python_version"]
    zip_file_S3key = f"{python_version}/{combined_package_name}.zip"
    license_info = "Refer for individual package"

    archive_path = combine_packages(
        packages=packages,
        python_version=python_version,
        combined_name=combined_package_name,
    )
    upload_to_s3(archive_path=archive_path, s3_location=zip_file_S3key)

    regions = get_from_common_service(resource=f"/api/v1/config/{python_version}/rgns")
    logger.info({"regions": regions})

    layers = publish_layer(
        regions=regions,
        archive_path=archive_path,
        python_version=python_version,
        license_info=license_info,
        combined_name=combined_package_name,
    )

    return layers


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


def publish_layer(
    regions: list[str],
    archive_path: str,
    python_version: str,
    combined_name: str,
    license_info: str,
):
    """
    Args:
        regions: List of regions to deploy to
        archive_path: Location of zip file to be uploaded to S3 bucket
        combined_name: Name of combined package
    returns:
        layer_arns: List of layer ARNs deployed
    """

    layer_name = f"{os.environ['LAMBDA_LAYER_PREFIX']}{python_version.replace('.','')}-{combined_name}"

    with open(archive_path, "rb") as zip_file:
        zip_binary = zip_file.read()

    layer_arns = []

    for region in regions:
        logger.info(
            {"message": "Deploying", "region": region, "package": combined_name}
        )
        lambda_client = boto3.client("lambda", region_name=region)
        response = lambda_client.publish_layer_version(
            LayerName=layer_name,
            Description=f"{combined_name}",
            Content={"ZipFile": zip_binary},
            CompatibleRuntimes=get_compatible_runtimes(python_version=python_version),
            CompatibleArchitectures=get_compatible_architectures(
                python_version=python_version
            ),
            LicenseInfo=license_info,
        )
        layer_version_arn = response["LayerVersionArn"]
        layer_arns.append(layer_version_arn)
        layer_version = int(layer_version_arn.split(":")[-1])

        # Make Layer Publicly accessible
        logger.info(
            {
                "message": "Making Public",
                "region": region,
                "package": combined_name,
                "python_version": python_version,
                "arn": layer_version_arn,
            }
        )
        lambda_client.add_layer_version_permission(
            LayerName=layer_name,
            VersionNumber=layer_version,
            StatementId="make_public",
            Action="lambda:GetLayerVersion",
            Principal="*",
        )

    logger.info({"message": "Layer ARNs", "layer_arns": layer_arns})

    return layer_arns
