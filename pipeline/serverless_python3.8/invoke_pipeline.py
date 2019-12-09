import os
import json
from datetime import datetime

import boto3

import get_config


def main(event, context):

    """
    Args:
      package: Python Package to build and deploy
    return:
      execution_arn: ARN of the state machine execution that is building the package
    """

    packages = get_config.get_packages()

    execution_arns =[]

    for package in packages:

        client = boto3.client('stepfunctions')
        execution_time = datetime.now().isoformat().replace('-', '').replace(':', '')[:14]
        response = client.start_execution(
            stateMachineArn=os.environ['PIPELINE_ARN'],
            name=f"{package}_{execution_time}",
            input=json.dumps({"package": package})
        )

        execution_arns.append(response['executionArn'])

    return {"arns": execution_arns}
