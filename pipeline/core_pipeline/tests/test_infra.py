import os

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

from infra import CorePipelineStack


@pytest.fixture
def stack():
    os.environ["KLAYERS_OFFLINE_SYNTH"] = "1"
    app = cdk.App()
    stage = "Klayers-prodp38"
    region = "us-east-2"
    cron_expr = "cron(0 2 1 * ? *)"

    stack = CorePipelineStack(
        app,
        f"klayers-core-{stage}",
        stage=stage,
        region=region,
        cron_expr=cron_expr,
        env=cdk.Environment(account="770693421928", region=region),
    )
    return stack


def test_lambda_counts(stack):
    template = Template.from_stack(stack)

    # 10 Zip Lambdas + 6 Dynamic Container Lambdas = 16
    template.resource_count_is("AWS::Lambda::Function", 16)

    # 1 Self-Contained Dependency Layer
    template.resource_count_is("AWS::Lambda::LayerVersion", 1)


def test_container_lambdas(stack):
    template = Template.from_stack(stack)

    # Container build lambdas should have 1769MB memory and 600s timeout
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "PackageType": "Image",
            "MemorySize": 1769,
            "Timeout": 600,
        },
    )

    # Arm64 container lambdas should have Architecture arm64
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "PackageType": "Image",
            "Architectures": ["arm64"],
        },
    )


def test_step_function_and_dynamic_choices(stack):
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::StepFunctions::StateMachine", 1)

    # Fetch StateMachine definition
    state_machines = template.find_resources("AWS::StepFunctions::StateMachine")
    sm_props = next(iter(state_machines.values()))["Properties"]
    def_string = sm_props["DefinitionString"]

    # In CDK, DefinitionString is a Fn::Join or string
    def_json_str = def_string
    if isinstance(def_string, dict) and "Fn::Join" in def_string:
        def_json_str = "".join([part if isinstance(part, str) else "{}" for part in def_string["Fn::Join"][1]])

    # Verify ChoicePythonVersion choices cover all 6 python versions from config.json
    for py_ver in ["p3.12", "p3.12-arm64", "p3.13", "p3.13-arm64", "p3.14", "p3.14-arm64"]:
        assert py_ver in def_json_str

    # Verify retry policies contain container conflict and timeout errors
    assert "Lambda.CodeArtifactUserPendingException" in def_json_str
    assert "Lambda.ResourceConflictException" in def_json_str


def test_event_bridge_rules(stack):
    template = Template.from_stack(stack)

    # We expect 5 EventBridge rules:
    # 1. InvokePipelineScheduleRule
    # 2. LayerDeleteRule
    # 3. PostMessageToSlackRule
    # 4. TriggerPipelineRule
    # 5. PipelineStatusFailureRule
    template.resource_count_is("AWS::Events::Rule", 5)

    # Schedule rule
    template.has_resource_properties(
        "AWS::Events::Rule",
        {"ScheduleExpression": "cron(0 2 1 * ? *)"},
    )

    # Layer delete rule
    template.has_resource_properties(
        "AWS::Events::Rule",
        {
            "EventPattern": {
                "detail-type": ["REMOVE"],
                "detail": {"pk_type": ["lyr"]},
            }
        },
    )

    # Status failure rule
    template.has_resource_properties(
        "AWS::Events::Rule",
        {
            "EventPattern": {
                "source": ["aws.states"],
                "detail-type": ["Step Functions Execution Status Change"],
                "detail": {
                    "status": ["ABORTED", "FAILED", "TIMED_OUT"],
                },
            }
        },
    )


def test_dynamodb_stream_event_source_mapping(stack):
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Lambda::EventSourceMapping", 1)
    template.has_resource_properties(
        "AWS::Lambda::EventSourceMapping",
        {
            "BatchSize": 10,
            "StartingPosition": "LATEST",
        },
    )
