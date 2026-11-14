import json

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from infra import GhPushStack


def test_gh_push_stack():
    app = cdk.App()
    stack = GhPushStack(
        app,
        "TestGhPushStack",
        stage="Klayers-prodp38",
        env=cdk.Environment(account="770693421928", region="us-east-2"),
    )
    template = Template.from_stack(stack)

    # 1. Assert exactly 6 Lambda functions exist
    template.resource_count_is("AWS::Lambda::Function", 6)

    # Assert all functions use Python 3.13 and 256 MB memory
    functions = template.find_resources("AWS::Lambda::Function")
    for _, fn_props in functions.items():
        assert fn_props["Properties"]["Runtime"] == "python3.13"
        assert fn_props["Properties"]["MemorySize"] == 256

    # 2. Assert State Machine exists and has ItemProcessor
    template.resource_count_is("AWS::StepFunctions::StateMachine", 1)
    state_machines = template.find_resources("AWS::StepFunctions::StateMachine")
    for _, sm_props in state_machines.items():
        assert sm_props["Properties"]["StateMachineName"] == "gh-push-pipeline"
        def_str = sm_props["Properties"]["DefinitionString"]
        # The definition string is a Fn::Join or string containing ItemProcessor
        def_joined = json.dumps(def_str)
        assert "ItemProcessor" in def_joined
        assert "MapPythonVersions" in def_joined
        assert "CheckPythonVersion" in def_joined
        assert "InvokePipelines" in def_joined
        assert "LoadConfig" in def_joined
        assert "UpdatePR" in def_joined

    # 3. Assert SSM Parameter for PipelineArn
    template.has_resource_properties(
        "AWS::SSM::Parameter",
        {
            "Name": "/gh-push/Klayers-prodp38/PipelineArn",
            "Type": "String",
            "Description": "Arn of Pipeline step function",
        },
    )

    # 4. Assert CloudFormation Output for PipelineArn
    template.has_output(
        "PipelineArn",
        {
            "Description": "The ARN of the example state machine",
        },
    )

    # 5. Assert IAM policies for dynamic CommonService URL resolution
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Action": "ssm:GetParameter",
                                "Effect": "Allow",
                                "Resource": (
                                    "arn:aws:ssm:us-east-2:770693421928:"
                                    "parameter/common-service/Klayers-prodp38/*"
                                ),
                            }
                        ),
                        Match.object_like(
                            {
                                "Action": "execute-api:Invoke",
                                "Effect": "Allow",
                                "Resource": "arn:aws:execute-api:us-east-2:770693421928:*/*",
                            }
                        ),
                    ]
                )
            }
        },
    )
