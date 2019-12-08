import os
import csv


def get_aws_regions():
    """
    Args:
        os.environ['STAGE'] set to current stage of running lambda
    returns:
        aws_regions : List of all regions to deploy lambdas into
    """

    with open(f"config/{os.environ['STAGE']}/regions.csv", 'r') as region_file:
        csv_reader = csv.DictReader(region_file)
        aws_regions = [line['Code'] for line in csv_reader]

    return aws_regions


def get_packages():
    """
    returns:
        packages: list of all packages to be built
    """

    with open(f"config/{os.environ['STAGE']}/packages.csv", 'r') as package_file:
        csv_reader = csv.DictReader(package_file)
        packages = [line['Package_Name'] for line in csv_reader]

    return packages
