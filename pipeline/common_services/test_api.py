import boto3
import os
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth


def main(event, context):
    """
    Test the common service APIs
    """
    api_url = get_api_url()
    response = call_api(url=api_url)
    
    return response

def get_api_url() -> str:
    """
    Get the API URL from SSM Parameter Store
    return:
        URL: API URL in the form of 'https://abcde.execute-api..../'
    """
    service = "common-service"
    stage = os.environ['STAGE']
    param = f"{service}/{stage}/CommonServiceApi/URL"

    client = boto3.client('ssm')
    response = client.get_parameter(
        Name=param,
        WithDecryption=False
    )
    return response['Parameter']['Value']


def call_api(url: str):
    auth = BotoAWSRequestsAuth(
        aws_host=url.split("/")[2],
        aws_region=os.environ['AWS_REGION'],
        aws_service='execute-api'
    )

    
    response = requests.get(
        f"{url}/api/v1/python-versions",
        auth=auth
    )
    return response.text