import os
import json
import requests
import shutil
import logging
import hashlib

import boto3
from botocore.exceptions import ClientError

from packaging.version import parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def freeze_requirements(package, path, version):
    """
    Walks through path, looking for *.dist-info folders. Parses out the package name and versions
    returns: package name and version in requirements.txt format as a string
    """

    requirements = []
    for subdir, dirs, files in os.walk(path):
        for dir in dirs:
            if (str(dir)[-10:]) == '.dist-info':
                package_info = str(dir)[:-10].split('-')
                package_name = package_info[0]
                package_version = package_info[1]
                requirements.append(f"{package_name}=={package_version}")

    requirements_txt = '\n'.join(sorted(requirements))
    requirements_hash = hashlib.sha256(requirements_txt.encode('utf-8')).hexdigest()

    dynamodb = boto3.client('dynamodb')
    try:
        dynamodb.put_item(TableName=os.environ['REQS_DB'],
                          Item={'package': {'S': package},
                                'version': {'S': str(version)},
                                'requirements': {'S': requirements_txt},
                                'requirements_hash': {'S': requirements_hash}})
        logger.info(f"Successfully written {package}:{version} status to DB with hash: {requirements_hash}")
    except ClientError as e:
        logger.info("Unexpected error Writing to DB: {}".format(e.response['Error']['Code']))

    return requirements_txt.strip(), requirements_hash


def upload_to_s3(zip_file, package):

    bucket_name = os.environ['BUCKET_NAME']

    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(zip_file, bucket_name, f'{package}.zip')

    client = boto3.client('s3')
    response = client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=package
    )

    logger.info(f"Uploaded {package}.zip with "
                f"size {response['Contents'][0]['Size']} "
                f"at {response['Contents'][0]['LastModified']} "
                f"to {bucket_name}")


def zip_dir(dir_path, package):
    zip_file = f'/tmp/{package}'
    result = shutil.make_archive(base_name=zip_file,
                                 format="zip",
                                 base_dir=dir_path.split('/')[-1],
                                 root_dir="/tmp")
    logger.info(result)
    return f"{zip_file}.zip"


def delete_dir(dir):
    try:
        shutil.rmtree(dir)
        logger.info("Deleted previous version of package directory")
    except FileNotFoundError:
        logger.info("No previous installation detected")
    return True


def dir_size(path='.'):
    total = 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += dir_size(entry.path)
    return total


def get_latest_release(package):
    """
    Args:
      package: Name of package to be queried
    returns:
      version: Version number of latest release that is **not**  a pre-release
    """
    req = requests.get(f"https://pypi.python.org/pypi/{package}/json")
    version = parse('0')
    if req.status_code == requests.codes.ok:
        j = json.loads(req.text)
        releases = j.get('releases', [])
        for release in releases:
            ver = parse(release)
            if not ver.is_prerelease:
                version = max(version, ver)

    return version


def install(package, package_dir):
    """"
    Args:
      package: Name of package to be queried
    return:
      path to zip file of final package
    """
    delete_dir(package_dir)
    import subprocess
    output = subprocess.run(["pip", "install", package, "-t", package_dir, '--quiet', '--upgrade', '--no-cache-dir'],
                            capture_output=True)
    logger.info(output)
    output = subprocess.run(["pip", "freeze", ">", "/tmp/requirements.txt"],
                            capture_output=True)
    return package_dir


def main(event,context):

    package = event['package']
    package_dir = f"/tmp/python"

    latest_release = get_latest_release(package)
    logger.info(f"Latest release for package {package} is {latest_release}")

    package_dir = install(package, package_dir=package_dir)
    package_size = dir_size(package_dir)
    logger.info(f"Installed {package} into {package_dir} with size: {package_size}")

    requirements_txt, requirements_hash = freeze_requirements(package=package,
                                                              path=package_dir,
                                                              version=latest_release)

    zip_file = zip_dir(dir_path=package_dir, package=package)
    logger.info(f"Zipped package info {zip_file}")

    logger.info("Uploading to S3")
    upload_to_s3(zip_file=zip_file, package=package)

    return json.dumps({"latest_release": str(latest_release),
                       "size": package_size,
                       "zip_size": os.path.getsize(zip_file),
                       "requirements.txt": requirements_txt,
                       "requirements_hash": requirements_hash})

