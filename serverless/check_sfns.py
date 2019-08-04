import boto3

""" NOT YET IMPLEMENTED """

def main(event, context):
    """
    Args:
        execution_arns: List of executions to check status on
    return:
        execution_complete: Boolean flag to signal if ALL executions are complete or not
    """

    client = boto3.client('stepfunctions')
    arns = event['execution_arns']

    for arn in arns:
        response = client.describe_execution(executionArn=arn)
        if response['status'] == 'RUNNING':
            break
        else:
            arns.remove(arn)
    else:
        # no break = all executions no longer running
        return {'execution_complete': True}

    # a break occurred
    return {'execution_complete': False,
            'execution_arns': arns}
