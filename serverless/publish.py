import os
import logging

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main(event, context):

    """
    Gets latest requirements.txt contents from dynamoDB and publishes to S3 bucket under requirements/<package>.txt
    """

    package = event['package']
    version = event['version']
    requirements_hash = event['requirements_hash']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['REQS_DB'])
    bucket = os.environ['BUCKET_NAME']

    response = table.get_item(Key={"package": package,
                                   "requirements_hash": requirements_hash})

    logger.info(f"Obtained requirements.txt file for {package}=={version}")
    requirements_txt = response['Item']['requirements']

    logger.info(f"Uploading to S3 Bucket")
    client = boto3.client('s3')
    client.put_object(Body=requirements_txt.encode('utf-8'),
                      Bucket=bucket,
                      Key=f'requirements/{package}.txt')

    return requirements_txt