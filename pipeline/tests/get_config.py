import json
import boto3


def get_config(stage="Klayers-defaultp38"):
    with open("pipeline/Terraform/terraform.tfvars.json", "r") as config_file:
        full_config = json.loads(config_file.read())

    config = dict()
    for key in full_config.keys():
        config[key] = full_config[key][stage]

    session = boto3.session.Session(
        profile_name=config["aws_profile"], region_name=config["aws_region"]
    )
    client = session.client("cloudformation")

    # Get stack resources
    stack_name = f"{config['app_name']}-{stage}"
    kwargs = {"StackName": stack_name}
    stack_resources = list()
    while True:
        response = client.list_stack_resources(**kwargs)
        stack_resources.extend(response["StackResourceSummaries"])
        try:
            kwargs["NextToken"] = response["NextToken"]
        except KeyError:
            break
    step_function_resource_ids = [
        stack_resource["PhysicalResourceId"]
        for stack_resource in stack_resources
        if stack_resource["ResourceType"] == "AWS::StepFunctions::StateMachine"
    ]

    config["step_functions_arn"] = dict()
    for id in step_function_resource_ids:
        name = id.split("-")[-1]
        config["step_functions_arn"][name] = id

    return config, session
