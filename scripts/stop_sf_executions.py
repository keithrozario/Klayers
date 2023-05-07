import boto3


if __name__ == "__main__":
    boto3.setup_default_session(profile_name="KlayersProdP38")

    client = boto3.client('stepfunctions')
    response = client.list_executions(
        stateMachineArn='arn:aws:states:us-east-2:770693421928:stateMachine:kl-Klayers-prodp38-pipeline',
        statusFilter='RUNNING',
    )

    if len(response['executions']) > 0:

        for execution in response['executions']:
            executionArn = execution['executionArn']
            response = client.stop_execution(
                executionArn=executionArn,
                error='01',
                cause='manualTermination'
            )
    else:
        print("No MOre executions left")
