import os
import csv
import json
import boto3
from aws_lambda_powertools.logging import Logger
from common.get_config import get_config_items

logger = Logger()
s3 = boto3.client('s3')
config_file_name = 'config.json'

@logger.inject_lambda_context
def main(event, context):
    
    python_version = event
    logger.info({'python_version': python_version})

    packages_in_dynamo = get_config_items(config_type="pckgs", python_version=python_version)
    logger.info({f'packages_in_dynamo': packages_in_dynamo})

    s3.download_file(os.getenv('CONFIG_BUCKET'), config_file_name, f'/tmp/{config_file_name}')
    with open(f'/tmp/{config_file_name}', 'r') as config_file:
        python_package_file_name = json.loads(config_file.read())[python_version]['packages_file']
    
    
    s3.download_file(os.getenv('CONFIG_BUCKET'), python_package_file_name, f'/tmp/{python_package_file_name}')
    with open(f'/tmp/{python_package_file_name}', 'r') as python_package_file:
        csv_reader = csv.DictReader(python_package_file)
        packages_in_csv = [line["Package_Name"] for line in csv_reader]
        logger.info({'packages_in_csv': packages_in_csv})
    
    new_packages = [pckg for pckg in packages_in_csv if pckg not in packages_in_dynamo]
    logger.info({'new_packages': new_packages})

    deleted_packages = [pckg for pckg in packages_in_dynamo if pckg not in packages_in_csv]
    logger.info({'deleted_packages': deleted_packages})

    return {
        'new_packages': new_packages,
        'deleted_packages': deleted_packages
    }
