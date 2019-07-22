import os
import json
import uuid

import boto3
import requests


def main(event, context):

    """
    Args:
      package: Python Package to build and deploy
    return:
      execution_arn: ARN of the state machine execution that is building the package
    """

    package = event['package']

    client = boto3.client('stepfunctions')
    response = client.start_execution(
        stateMachineArn=os.environ['PIPELINE_ARN'],
        name=str(uuid.uuid4()).replace('-', 'X'),  # name cannot contain '-'
        input=json.dumps({"input": {"package": package}})
    )

    execution_arn = response['executionArn']

    return execution_arn
