import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_ecr as ecr,
)
from aws_cdk import (
    aws_events as events,
)
from aws_cdk import (
    aws_events_targets as targets,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from aws_cdk import (
    aws_logs as logs,
)
from aws_cdk import (
    aws_ssm as ssm,
)
from aws_cdk import (
    aws_stepfunctions as sfn,
)
from aws_cdk import (
    aws_stepfunctions_tasks as tasks,
)
from constructs import Construct

STAGE_ACCOUNTS = {
    "Klayers-defaultp38": "367660174341",
    "Klayers-devp38": "908645878701",
    "Klayers-prodp38": "770693421928",
}


def build_deps_layer(scope: Construct) -> lambda_.LayerVersion:
    """Builds a self-contained Lambda layer containing runtime dependencies.

    Uses `uv pip install` into `.layer_build/python`. Zero external layer ARNs.
    """
    base_dir = Path(__file__).resolve().parent
    layer_dir = base_dir / ".layer_build"
    python_dir = layer_dir / "python"
    req_file = base_dir / "requirements.txt"
    marker_file = python_dir / ".installed"

    should_build = True
    if (
        marker_file.exists()
        and req_file.exists()
        and marker_file.stat().st_mtime >= req_file.stat().st_mtime
    ):
        should_build = False

    if should_build:
        python_dir.mkdir(parents=True, exist_ok=True)
        uv_bin = shutil.which("uv") or "uv"
        subprocess.run(
            [
                uv_bin,
                "pip",
                "install",
                "--quiet",
                "--python-platform",
                "x86_64-manylinux2014",
                "--python-version",
                "3.13",
                "--target",
                str(python_dir),
                "-r",
                str(req_file),
            ],
            check=True,
        )
        marker_file.touch()

    return lambda_.LayerVersion(
        scope,
        "CorePipelineDepsLayer",
        code=lambda_.Code.from_asset(str(layer_dir)),
        compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
        description="Shared dependencies for Klayers core pipeline Lambdas",
    )


def resolve_ecr_image(stage: str, region: str, account_id: str, py_param: str, arch: str) -> tuple[str, str]:
    """Resolves ECR repo name and digest from SSM at synth time under active credentials.

    Falls back cleanly to mock values if KLAYERS_OFFLINE_SYNTH=1 or credentials are not active.
    """
    fallback_repo = f"{py_param}{arch}build"
    fallback_digest = "sha256:" + "0" * 64

    if os.environ.get("KLAYERS_OFFLINE_SYNTH") == "1":
        return fallback_repo, fallback_digest

    try:
        import boto3

        ssm_client = boto3.client("ssm", region_name=region)
        repo_param = f"/kl/{stage}/build/{py_param}/{arch}/repo"
        digest_param = f"/kl/{stage}/build/{py_param}/{arch}/digest"

        resp = ssm_client.get_parameters(Names=[repo_param, digest_param])
        params = {p["Name"]: p["Value"] for p in resp.get("Parameters", [])}

        if repo_param not in params or digest_param not in params:
            print(
                f"WARNING: Missing SSM parameters for {py_param}/{arch} in {stage} ({region}); using placeholder digest.",
                file=sys.stderr,
            )
            return fallback_repo, fallback_digest

        repo_val = params[repo_param]
        repo_name = repo_val.split("/")[-1]

        digest_val = params[digest_param].strip()
        if not digest_val.startswith("sha256:"):
            digest_val = f"sha256:{digest_val}"

        return repo_name, digest_val
    except Exception as exc:  # noqa: BLE001
        print(
            f"WARNING: Could not resolve SSM ECR digest for {py_param}/{arch} ({exc}); using placeholder digest.",
            file=sys.stderr,
        )
        return fallback_repo, fallback_digest


def parse_python_version(py_ver: str) -> tuple[str, str, str]:
    """Returns (py_param, arch, state_suffix).

    e.g. 'p3.12' -> ('p312', 'x86', '312')
         'p3.12-arm64' -> ('p312', 'arm64', '312arm64')
    """
    is_arm = py_ver.endswith("-arm64")
    base = py_ver.replace("-arm64", "")
    py_param = base.replace(".", "")
    digits = base.replace("p", "").replace(".", "")
    state_suffix = f"{digits}arm64" if is_arm else digits
    arch = "arm64" if is_arm else "x86"
    return py_param, arch, state_suffix


class CorePipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str, region: str, cron_expr: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        account_id = self.account
        src_dir = str(Path(__file__).resolve().parent / "src")
        code = lambda_.Code.from_asset(src_dir)
        deps_layer = build_deps_layer(self)

        # SSM parameter lookups (CFn dynamic references)
        layers_bucket_name = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/layers_bucket/name")
        layers_bucket_arn = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/layers_bucket/arn")
        config_bucket_name = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/config_bucket/name")
        db_name = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/db-ver2/name")
        db_arn = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/db-ver2/arn")
        db_stream_label = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/db-ver2/stream/label")
        db_stream_arn = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/db-ver2/stream/arn")

        slack_token_param = f"/kl/{stage}/slack_token"

        # Read config.json for dynamic python versions
        config_path = Path(__file__).resolve().parent.parent / "config" / "config.json"
        with open(config_path) as f:
            config_data = json.load(f)
        python_versions: list[str] = config_data.get("python_versions", [])

        def make_log_group(log_id: str) -> logs.LogGroup:
            return logs.LogGroup(
                self,
                log_id,
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=RemovalPolicy.DESTROY,
            )

        # ---------------------------------------------------------------------------
        # Container Build Lambdas
        # ---------------------------------------------------------------------------
        build_lambdas: dict[str, lambda_.IFunction] = {}
        for py_ver in python_versions:
            py_param, arch, state_suffix = parse_python_version(py_ver)
            repo_name, digest = resolve_ecr_image(stage, region, account_id, py_param, arch)

            ecr_repo = ecr.Repository.from_repository_name(self, f"BuildEcrRepo-{py_ver}", repo_name)
            docker_code = lambda_.DockerImageCode.from_ecr(ecr_repo, tag_or_digest=digest)

            lambda_arch = lambda_.Architecture.ARM_64 if arch == "arm64" else lambda_.Architecture.X86_64

            build_fn = lambda_.DockerImageFunction(
                self,
                f"Build{state_suffix.capitalize()}Function",
                code=docker_code,
                architecture=lambda_arch,
                timeout=Duration.seconds(600),
                memory_size=1769,
                log_group=make_log_group(f"Build{state_suffix.capitalize()}LogGroup"),
                description=f"Builds package in container for {py_ver} then uploads to S3",
                environment={
                    "STAGE": stage,
                    "LOG_LEVEL": "INFO",
                    "DB_NAME": db_name,
                    "BUCKET_NAME": layers_bucket_name,
                },
            )

            build_fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["s3:PutObject", "s3:PutObjectAcl"],
                    resources=[f"{layers_bucket_arn}/*"],
                )
            )
            build_fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["s3:ListBucket"],
                    resources=[layers_bucket_arn],
                )
            )
            build_fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:GetItem"],
                    resources=[db_arn],
                )
            )

            build_lambdas[py_ver] = build_fn

        # ---------------------------------------------------------------------------
        # 10 Zip Lambdas (Python 3.13)
        # ---------------------------------------------------------------------------

        # 1. invoke_pipeline
        invoke_pipeline_fn = lambda_.Function(
            self,
            "InvokePipelineFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="01_invoke_pipelines/invoke_pipelines.main",
            code=code,
            layers=[deps_layer],
            timeout=Duration.seconds(900),
            memory_size=256,
            log_group=make_log_group("InvokePipelineLogGroup"),
            description="Invoke multiple pipelines, one for each package",
            environment={
                "STAGE": stage,
                "LOG_LEVEL": "INFO",
                "DB_NAME": db_name,
                "BUCKET_NAME": layers_bucket_name,
                "POWERTOOLS_SERVICE_NAME": "Klayers.invoke_pipeline",
                "LAMBDA_LAYER_PREFIX": "Klayers-",
                "CONFIG_BUCKET": config_bucket_name,
            },
        )
        invoke_pipeline_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=[f"arn:aws:events:{region}:{account_id}:event-bus/default"],
            )
        )
        invoke_pipeline_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem"],
                resources=[db_arn],
            )
        )
        invoke_pipeline_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:{region}:{account_id}:parameter/common-service/{stage}/*"],
            )
        )
        invoke_pipeline_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:Invoke"],
                resources=[f"arn:aws:execute-api:{region}:{account_id}:*/*"],
            )
        )

        events.Rule(
            self,
            "InvokePipelineScheduleRule",
            schedule=events.Schedule.expression(cron_expr),
            targets=[targets.LambdaFunction(invoke_pipeline_fn)],
        )

        # 2. check
        check_fn = lambda_.Function(
            self,
            "CheckFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="02_pipeline/check.main",
            code=code,
            layers=[deps_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
            log_group=make_log_group("CheckLogGroup"),
            description="Checks for package on PyPi via the API",
            environment={
                "STAGE": stage,
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": stage,
            },
        )

        # 3. deploy
        deploy_fn = lambda_.Function(
            self,
            "DeployFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="02_pipeline/deploy.main",
            code=code,
            layers=[deps_layer],
            timeout=Duration.seconds(600),
            memory_size=512,
            log_group=make_log_group("DeployLogGroup"),
            description="Deploys functions to multiple regions",
            environment={
                "STAGE": stage,
                "LOG_LEVEL": "INFO",
                "DB_NAME": db_name,
                "BUCKET_NAME": layers_bucket_name,
                "POWERTOOLS_SERVICE_NAME": "Klayers.Deploy",
                "EXPIRY_DAYS": "365",
            },
        )
        deploy_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:Query",
                    "dynamodb:UpdateItem",
                ],
                resources=[db_arn, f"{db_arn}/index/package_global_by_python_version"],
            )
        )
        deploy_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "lambda:AddLayerVersionPermission",
                    "lambda:GetLayerVersion",
                    "lambda:PublishLayerVersion",
                ],
                resources=["*"],
            )
        )
        deploy_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{layers_bucket_arn}/*"],
            )
        )
        deploy_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:{region}:{account_id}:parameter/common-service/{stage}/*"],
            )
        )
        deploy_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:Invoke"],
                resources=[f"arn:aws:execute-api:{region}:{account_id}:*/*"],
            )
        )

        # 4. combine_packages
        combine_packages_fn = lambda_.Function(
            self,
            "CombinePackagesFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="02_pipeline/combine.main",
            code=code,
            layers=[deps_layer],
            timeout=Duration.seconds(600),
            memory_size=1769,
            log_group=make_log_group("CombinePackagesLogGroup"),
            description="Combines multiple packages into a single zip file",
            environment={
                "STAGE": stage,
                "LOG_LEVEL": "INFO",
                "DB_NAME": db_name,
                "BUCKET_NAME": layers_bucket_name,
                "POWERTOOLS_SERVICE_NAME": stage,
            },
        )
        combine_packages_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject", "s3:PutObjectAcl", "s3:GetObject"],
                resources=[f"{layers_bucket_arn}/*"],
            )
        )
        combine_packages_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"],
                resources=[layers_bucket_arn],
            )
        )
        combine_packages_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "lambda:AddLayerVersionPermission",
                    "lambda:GetLayerVersion",
                    "lambda:PublishLayerVersion",
                ],
                resources=["*"],
            )
        )
        combine_packages_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:{region}:{account_id}:parameter/common-service/{stage}/*"],
            )
        )
        combine_packages_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:Invoke"],
                resources=[f"arn:aws:execute-api:{region}:{account_id}:*/*"],
            )
        )

        # 5. stream_handler
        stream_handler_fn = lambda_.Function(
            self,
            "StreamHandlerFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="04_stream_processor/stream_processor.main",
            code=code,
            layers=[deps_layer],
            timeout=Duration.seconds(20),
            memory_size=256,
            log_group=make_log_group("StreamHandlerLogGroup"),
            description="Triggered on every change to db",
            environment={
                "STAGE": stage,
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "Klayers.StreamEvent",
                "STREAM_LABEL": db_stream_label,
            },
        )
        stream_handler_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=[f"arn:aws:events:{region}:{account_id}:event-bus/default"],
            )
        )
        stream_handler_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:DescribeStream",
                    "dynamodb:GetRecords",
                    "dynamodb:GetShardIterator",
                    "dynamodb:ListStreams",
                ],
                resources=[db_stream_arn],
            )
        )

        lambda_.EventSourceMapping(
            self,
            "StreamHandlerEventSourceMapping",
            target=stream_handler_fn,
            event_source_arn=db_stream_arn,
            starting_position=lambda_.StartingPosition.LATEST,
            batch_size=10,
        )

        # 6. layer_delete
        layer_delete_fn = lambda_.Function(
            self,
            "LayerDeleteFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="04_stream_processor/layer_delete.main",
            code=code,
            layers=[deps_layer],
            timeout=Duration.seconds(20),
            memory_size=256,
            log_group=make_log_group("LayerDeleteLogGroup"),
            description="Delete Layers from regions",
            environment={
                "STAGE": stage,
                "LOG_LEVEL": "DEBUG",
                "DB_NAME": db_name,
                "POWERTOOLS_SERVICE_NAME": "Klayers.DeleteEvent",
            },
        )
        layer_delete_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["lambda:DeleteLayerVersion"],
                resources=["*"],
            )
        )
        layer_delete_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:PutItem"],
                resources=[db_arn],
            )
        )

        events.Rule(
            self,
            "LayerDeleteRule",
            event_pattern=events.EventPattern(
                source=[db_stream_label],
                detail_type=["REMOVE"],
                detail={"pk_type": ["lyr"]},
            ),
            targets=[targets.LambdaFunction(layer_delete_fn)],
        )

        # Slack Lambdas
        slack_env = {
            "STAGE": stage,
            "SLACK_TOKEN_PARAMETER": slack_token_param,
        }
        slack_ssm_policy = iam.PolicyStatement(
            actions=["ssm:GetParameter"],
            resources=[f"arn:aws:ssm:{region}:{account_id}:parameter{slack_token_param}"],
        )

        # 7. slack_pipeline
        slack_pipeline_fn = lambda_.Function(
            self,
            "SlackPipelineFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="05_slack_notification/slack_notification.slack_notification_pipeline_error",
            code=code,
            layers=[deps_layer],
            timeout=Duration.seconds(20),
            memory_size=256,
            log_group=make_log_group("SlackPipelineLogGroup"),
            description="Notify Slack when there's an error on the pipeline state machine",
            environment={
                **slack_env,
                "POWERTOOLS_SERVICE_NAME": "slack_pipeline",
            },
        )
        slack_pipeline_fn.add_to_role_policy(slack_ssm_policy)

        # 8. slack_publish
        slack_publish_fn = lambda_.Function(
            self,
            "SlackPublishFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="05_slack_notification/slack_notification.slack_notification_publish",
            code=code,
            layers=[deps_layer],
            timeout=Duration.seconds(20),
            memory_size=256,
            log_group=make_log_group("SlackPublishLogGroup"),
            description="Notify Slack when a publish is successful or failed",
            environment={
                **slack_env,
                "POWERTOOLS_SERVICE_NAME": "slack_publish",
            },
        )
        slack_publish_fn.add_to_role_policy(slack_ssm_policy)

        # 9. post_message_to_slack
        post_message_to_slack_fn = lambda_.Function(
            self,
            "PostMessageToSlackFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="05_slack_notification/slack_notification.post_message_to_slack",
            code=code,
            layers=[deps_layer],
            timeout=Duration.seconds(20),
            memory_size=256,
            log_group=make_log_group("PostMessageToSlackLogGroup"),
            description="Generic Slack notifications via EventBridge",
            environment={
                **slack_env,
                "POWERTOOLS_SERVICE_NAME": "post_to_slack",
            },
        )
        post_message_to_slack_fn.add_to_role_policy(slack_ssm_policy)

        events.Rule(
            self,
            "PostMessageToSlackRule",
            event_pattern=events.EventPattern(
                detail_type=["post_to_slack"],
            ),
            targets=[targets.LambdaFunction(post_message_to_slack_fn)],
        )

        # 10. slack_invokepipeline
        slack_invokepipeline_fn = lambda_.Function(
            self,
            "SlackInvokePipelineFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="05_slack_notification/slack_notification.slack_notification_invoke_pipeline_error",
            code=code,
            layers=[deps_layer],
            timeout=Duration.seconds(20),
            memory_size=256,
            log_group=make_log_group("SlackInvokePipelineLogGroup"),
            description="Notify Slack when there's an error on the invoke pipeline state machine",
            environment={
                **slack_env,
                "POWERTOOLS_SERVICE_NAME": "slack_invoke_pipeline",
            },
        )
        slack_invokepipeline_fn.add_to_role_policy(slack_ssm_policy)

        # ---------------------------------------------------------------------------
        # Step Function (kl-${stage}-pipeline)
        # ---------------------------------------------------------------------------
        done_state = sfn.Succeed(self, "Done")
        check_fail_state = sfn.Fail(self, "CheckFail", error="CheckFailure", cause="Unknown")
        build_fail_state = sfn.Fail(self, "BuildFail", error="BuildFailure", cause="Unknown")
        deploy_fail_state = sfn.Fail(self, "DeployFail", error="DeployFailure", cause="Unknown")
        unknown_py_fail = sfn.Fail(
            self,
            "UnknownPythonVersion",
            error="UnknownPythonVersion",
            cause="UnknownPythonVersion",
        )

        deploy_task = tasks.LambdaInvoke(
            self,
            "Deploy",
            lambda_function=deploy_fn,
            payload_response_only=True,
        )
        deploy_task.add_retry(
            errors=[
                "States.Timeout",
                "Lambda.ClientExecutionTimeoutException",
                "Lambda.ServiceException",
                "Lambda.AWSLambdaException",
                "Lambda.SdkClientException",
                "Lambda.TooManyRequestsException",
            ],
            max_attempts=2,
            backoff_rate=30,
            interval=Duration.seconds(60),
        )
        deploy_task.add_catch(deploy_fail_state, errors=["States.ALL"])
        deploy_task.next(done_state)

        # Build tasks for each python version
        build_retry_errors = [
            "States.Timeout",
            "Lambda.ClientExecutionTimeoutException",
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "Lambda.TooManyRequestsException",
            "Lambda.ResourceConflictException",
            "Lambda.CodeArtifactUserPendingException",
        ]

        build_tasks: dict[str, sfn.TaskStateBase] = {}
        for py_ver in python_versions:
            _, _, state_suffix = parse_python_version(py_ver)
            state_name = f"Build{state_suffix}"
            build_fn = build_lambdas[py_ver]

            build_task = tasks.LambdaInvoke(
                self,
                state_name,
                lambda_function=build_fn,
                payload_response_only=True,
            )
            build_task.add_retry(
                errors=build_retry_errors,
                max_attempts=5,
                backoff_rate=2,
                interval=Duration.seconds(15),
            )
            build_task.add_catch(build_fail_state, errors=["States.ALL"])
            build_task.next(deploy_task)

            build_tasks[py_ver] = build_task

        choice_py_ver = sfn.Choice(self, "ChoicePythonVersion")
        for py_ver, b_task in build_tasks.items():
            choice_py_ver.when(
                sfn.Condition.string_equals("$.python_version", py_ver),
                b_task,
            )
        choice_py_ver.otherwise(unknown_py_fail)

        check_task = tasks.LambdaInvoke(
            self,
            "Check",
            lambda_function=check_fn,
            payload_response_only=True,
        )
        check_task.add_retry(
            errors=[
                "States.Timeout",
                "Lambda.ClientExecutionTimeoutException",
                "Lambda.ServiceException",
                "Lambda.AWSLambdaException",
                "Lambda.SdkClientException",
                "Lambda.TooManyRequestsException",
            ],
            max_attempts=5,
            backoff_rate=2,
            interval=Duration.seconds(15),
        )
        check_task.add_catch(check_fail_state, errors=["States.ALL"])
        check_task.next(choice_py_ver)

        random_delay = sfn.Wait(
            self,
            "RandomDelay",
            time=sfn.WaitTime.seconds_path("$.detail.secondsDelay"),
        )
        random_delay.next(check_task)

        pipeline_name = f"kl-{stage}-pipeline"
        state_machine = sfn.StateMachine(
            self,
            "PipelineStateMachine",
            state_machine_name=pipeline_name,
            definition_body=sfn.DefinitionBody.from_chainable(random_delay),
            timeout=Duration.hours(2),
        )

        # Trigger state machine from EventBridge
        events.Rule(
            self,
            "TriggerPipelineRule",
            event_pattern=events.EventPattern(
                source=[f"Klayers.invoke.{stage}"],
                detail_type=["invoke_pipeline"],
            ),
            targets=[targets.SfnStateMachine(state_machine)],
        )

        # Monitor state machine execution failures
        events.Rule(
            self,
            "PipelineStatusFailureRule",
            event_pattern=events.EventPattern(
                source=["aws.states"],
                detail_type=["Step Functions Execution Status Change"],
                detail={
                    "status": ["ABORTED", "FAILED", "TIMED_OUT"],
                    "stateMachineArn": [state_machine.state_machine_arn],
                },
            ),
            targets=[targets.LambdaFunction(slack_pipeline_fn)],
        )


app = cdk.App()
stage = app.node.try_get_context("stage") or os.environ.get("AWS_STAGE", "Klayers-defaultp38")

tfvars_path = Path(__file__).resolve().parent.parent / "Terraform" / "terraform.tfvars.json"
with open(tfvars_path) as f:
    tfvars = json.load(f)

region = tfvars.get("aws_region", {}).get(stage, "us-east-2")
cron_expr = tfvars.get("cron_expression_invoke_pipelines", {}).get(stage, "cron(0 2 1 * ? *)")
account_id = STAGE_ACCOUNTS.get(stage, "770693421928")

CorePipelineStack(
    app,
    f"klayers-core-{stage}",
    stage=stage,
    region=region,
    cron_expr=cron_expr,
    env=cdk.Environment(account=account_id, region=region),
)

app.synth()
