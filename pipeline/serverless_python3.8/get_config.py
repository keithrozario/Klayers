import tempfile
import os
import csv
import io

import boto3


def get_aws_regions():
    """
    Args:
        os.environ['BUCKET_NAME'] set to Bucket name to grab configuration from
    returns:
        aws_regions : List of all regions to deploy lambdas into
    """

    s3_client = boto3.client('s3')
    bucket_name = os.environ['BUCKET_NAME']

    with tempfile.TemporaryFile() as region_file:
        s3_client.download_fileobj(bucket_name, 'config/regions.csv', region_file)
        region_file.seek(0)
        file_as_string = region_file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(file_as_string))
        aws_regions = [line['Code'] for line in csv_reader]

    return aws_regions


def get_packages():
    """
    returns:
        packages: list of all packages to be built
    """

    s3_client = boto3.client('s3')
    bucket_name = os.environ['BUCKET_NAME']

    with tempfile.TemporaryFile() as package_file:
        s3_client.download_fileobj(bucket_name, 'config/packages.csv', package_file)
        package_file.seek(0)
        file_as_string = package_file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(file_as_string))
        packages = [line['Package_Name'] for line in csv_reader]

    return packages

