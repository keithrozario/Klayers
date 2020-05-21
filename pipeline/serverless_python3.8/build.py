import os
import shutil
import hashlib
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from aws_lambda_powertools.logging import logger_setup, logger_inject_lambda_context
logger = logger_setup()


def put_requirements_hash(package, version, requirements_txt, requirements_hash):
    """
    Args:
      package: Package name
      version: Package version
      requirements_hash: SHA256 hash of the requirements.txt file
      requirements_txt: requirements txt of the entire build
    returns:
      None
    """
    client = boto3.client('dynamodb')
    table_name = os.environ['DB_NAME']

    # Get latest build version for package
    response = client.get_item(
        TableName=table_name,
        Key={'pk': {'S': 'v0'}, 'sk': {'S': package}},
        ProjectionExpression="bltVrsn",
    )
    try:
        latest_version = response['Item']['bltVrsn']['S']
        new_version = f"{latest_version[0]}{int(latest_version[1:])+1}"
    except KeyError:
        # Version wasn't deployed before, start with v1
        new_version = "v1"

    Item = {
        'pk': {'S': new_version},
        'sk': {'S': package},
        'pckgVrsn': {'S': str(version)},
        'rqrmntsTxt': {'S': requirements_txt},
        'rqrmntsHsh': {'S': requirements_hash},
        'bltVrsn': {'S': new_version},
        'created_date': {'S': datetime.utcnow().isoformat()},
    }

    # Insert new record
    try:
        response = client.transact_write_items(
            TransactItems=[
                {
                    'Update': {
                        'TableName': table_name,
                        'Key': {
                            'pk': {'S': 'v0.reqs'},
                            'sk': {'S': package},
                        },
                        'UpdateExpression':
                            "set "
                            "rqrmntsTxt = :rqrmntsTxt, "
                            "pckgVrsn = :pckgVrsn, "
                            "rqrmntsHsh = :rqrmntsHsh,"
                            "bltVrsn = :bltVrsn",
                        "ExpressionAttributeValues": {
                            ':rqrmntsTxt': {'S': requirements_txt},
                            ':pckgVrsn': {'S': str(version)},
                            ':rqrmntsHsh': {'S': requirements_hash},
                            ':bltVrsn': {'S': new_version},
                        },
                        'ConditionExpression': "bltVrsn <> :bltVrsn",
                    }
                },
                {
                    'Put': {
                        'TableName': table_name,
                        'Item': Item,
                    }
                }
            ])
        logger.info({"message": "Successfully written",
                     "item": Item})
        logger.debug(f"DynamoDB response: {response}")
    except ClientError as e:
        logger.error({
            "error_code": e.response['Error']['Code'],
            "error_message": e.response['Error']['Message'],
            "item": Item,
            "message": "Failed to Update record for Build Version"})
        exit(1)

    return

def check_requirement_hash(package, requirements_hash):
    """
    Args:
      package: Package name
      requirements_hash: SHA256 hash of the requirements.txt file
    returns:
      exists: Boolean value of if the requirements_hash exists in the DB (package was built already)
    """

    client = boto3.client('dynamodb')
    table_name = os.environ['DB_NAME']

    response = client.get_item(
        TableName=table_name,
        Key={'pk': {'S': 'v0'}, 'sk': {'S': package}},
        ProjectionExpression="rqrmntsHsh",
    )

    if requirements_hash == response.get('Item', {}).get('rqrmntsHsh', {}).get('S', False):
        hash_found = True
    else:
        hash_found = False

    return hash_found


def freeze_requirements(package, path):
    """
    Walks through path, looking for *.dist-info folders. Parses out the package name and versions
    returns: package name and version in requirements.txt format as a string
    """
    import subprocess

    logger.info("Getting requirements.txt file")
    os.environ['PYTHONPATH'] = '/opt/python'
    pip_install = subprocess.run(['pip', 'freeze', '--path', path], shell=False, capture_output=True)
    requirements_txt = pip_install.stdout.decode('utf-8').strip()
    logger.info(f"Requirements txt : \n{requirements_txt}")
    requirements_hash = hashlib.sha256(requirements_txt.encode('utf-8')).hexdigest()

    version = None
    for line in requirements_txt.split('\n'):
        if line[:len(package)].lower() == package.lower():
            version = line.split('==')[1]
            logger.info(f"Version of {package} found is {version}")
            break

    if version is None:
        logger.error("Unable to determine version of package....refer to logs for requirements.txt")
        exit(1)

    return requirements_txt, requirements_hash, version


def upload_to_s3(zip_file, package, uploaded_file_name):
    """
    Args:
      zip_file: Location of zip file to be uploaded to S3 bucket
      package: Name of python package being uploaded
    return:
      uploaded_file_name: Name of file in S3 bucket
    """

    bucket_name = os.environ['BUCKET_NAME']

    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(zip_file, bucket_name, uploaded_file_name)

    client = boto3.client('s3')
    response = client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=package
    )

    logger.info({
        "message": f"Uploaded {package}.zip", 
        "size": response['Contents'][0]['Size'],
        "time": response['Contents'][0]['LastModified'],
        "bucket": bucket_name})

    return uploaded_file_name


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
        logger.debug("Deleted previous version of package directory")
    except FileNotFoundError:
        logger.debug("No previous installation detected")
    return True


def dir_size(path='.'):
    total = 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += dir_size(entry.path)
    return total


def install(package, package_dir):
    """"
    Args:
      package: Name of package to be queried
    return:
      path to zip file of final package
    """
    delete_dir(package_dir)
    import subprocess
    os.environ['PYTHONPATH'] = '/opt/python'
    output = subprocess.run(["pip", "install", package, "-t", package_dir, '--quiet', '--upgrade', '--no-cache-dir'],
                            capture_output=True)
    logger.info(output)

    return package_dir

@logger_inject_lambda_context
def main(event,context):

    package = event['package']
    license_info = event['license_info']

    package_dir = f"/tmp/python"
    uploaded_file_name = f'{package}.zip'
    build_flag = False

    package_dir = install(package, package_dir=package_dir)
    package_size = dir_size(package_dir)
    logger.info({"package": package, "size": package_size})

    requirements_txt, requirements_hash, version = freeze_requirements(package=package,
                                                                       path=package_dir)
    logger.info({"message": "Built Package", "requirements_txt": requirements_txt})
    
    with open(f"{package_dir}/requirements.txt", 'w') as requirements_file:
        requirements_file.write(requirements_txt)
    zip_file = zip_dir(dir_path=package_dir,
                       package=package)

    if not check_requirement_hash(package=package,
                                  requirements_hash=requirements_hash):
        logger.info({"requirements_hash": requirements_hash, "package": package, "version": version, 
        "message": "Uploading to S3"})

        upload_to_s3(zip_file=zip_file,
                     package=package,
                     uploaded_file_name=uploaded_file_name)
        put_requirements_hash(package=package,
                              requirements_txt=requirements_txt,
                              requirements_hash=requirements_hash,
                              version=version)

        logger.info({
            "package": package,
            "version": version,
            "location": f"s3://{os.environ['BUCKET_NAME']}",
            "size": os.path.getsize(zip_file),
            "requirements_hash" : requirements_hash})
        build_flag = True

    else:
        build_flag = False
        logger.info("Requirements hash previously built, proceeding to check for deployment")

    return {"zip_file": uploaded_file_name,
            "package": package,
            "version": version,
            "requirements_hash": requirements_hash,
            "license_info": license_info,
            "build_flag": build_flag}
