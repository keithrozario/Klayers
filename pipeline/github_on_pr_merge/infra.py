import json
import os
import shutil
import subprocess
from pathlib import Path

import aws_cdk as cdk
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_logs as logs
import aws_cdk.aws_ssm as ssm
import aws_cdk.aws_stepfunctions as sfn
import aws_cdk.aws_stepfunctions_tasks as tasks
from constructs import Construct

STAGE_ACCOUNTS = {
    "Klayers-defaultp38": "367660174341",
    "Klayers-devp38": "908645878701",
    "Klayers-prodp38": "770693421928",
}


def build_deps_layer(scope: Construct) -> lambda_.LayerVersion:
    """Build a Lambda Layer containing all runtime requirements via uv."""
    base_dir = Path(__file__).parent.resolve()
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
        uv_path = shutil.which("uv") or "uv"
        cmd = [
            uv_path,
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
        ]
        subprocess.run(cmd, check=True)
        marker_file.touch()

    return lambda_.LayerVersion(
        scope,
        "DependenciesLayer",
        code=lambda_.Code.from_asset(str(layer_dir)),
        compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
        description="Internal dependencies layer for klayers-gh-push",
    )


class GhPushStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        account_id = self.account
        region = self.region

        # Resolve Terraform / Base SSM parameters
        db_arn = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/db-ver2/arn")
        db_name = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/db-ver2/name")
        config_bucket_arn = ssm.StringParameter.value_for_string_parameter(
            self, f"/kl/{stage}/config_bucket/arn"
        )
        config_bucket_name = ssm.StringParameter.value_for_string_parameter(
            self, f"/kl/{stage}/config_bucket/name"
        )

        # Build runtime dependencies layer
        deps_layer = build_deps_layer(self)

        # Common Lambda configuration
        src_path = str(Path(__file__).parent / "src")
        code = lambda_.Code.from_asset(src_path)

        common_env = {
            "STAGE": stage,
            "LOG_LEVEL": "INFO",
            "DB_NAME": db_name,
            "CONFIG_BUCKET": config_bucket_name,
        }

        # 1. check_new_packages
        fn_check_new_packages = lambda_.Function(
            self,
            "CheckNewPackagesFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="check_new_packages.main",
            code=code,
            timeout=cdk.Duration.seconds(120),
            memory_size=256,
            log_group=logs.LogGroup(
                self,
                "CheckNewPackagesLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
            environment={
                **common_env,
                "POWERTOOLS_SERVICE_NAME": "Klayers.on_push_master",
            },
            layers=[deps_layer],
            description="Compares S3 vs. DynamoDB packages and updates new config in Dynamo",
        )
        fn_check_new_packages.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem"],
                resources=[db_arn],
            )
        )
        fn_check_new_packages.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{config_bucket_arn}/*"],
            )
        )
        fn_check_new_packages.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:{region}:{account_id}:parameter/common-service/{stage}/*"],
            )
        )
        fn_check_new_packages.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:Invoke"],
                resources=[f"arn:aws:execute-api:{region}:{account_id}:*/*"],
            )
        )

        # 2. check_python_versions
        fn_check_python_versions = lambda_.Function(
            self,
            "CheckPythonVersionsFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="check_python_versions.main",
            code=code,
            timeout=cdk.Duration.seconds(120),
            memory_size=256,
            log_group=logs.LogGroup(
                self,
                "CheckPythonVersionsLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
            environment={
                **common_env,
                "POWERTOOLS_SERVICE_NAME": "Klayers.on_push_master",
            },
            layers=[deps_layer],
            description="Compares python versions",
        )
        fn_check_python_versions.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:{region}:{account_id}:parameter/common-service/{stage}/*"],
            )
        )
        fn_check_python_versions.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:Invoke"],
                resources=[f"arn:aws:execute-api:{region}:{account_id}:*/*"],
            )
        )

        # 3. invoke_pipelines
        fn_invoke_pipelines = lambda_.Function(
            self,
            "InvokePipelinesFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="invoke_pipelines.main",
            code=code,
            timeout=cdk.Duration.seconds(120),
            memory_size=256,
            log_group=logs.LogGroup(
                self,
                "InvokePipelinesLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
            environment={
                **common_env,
                "POWERTOOLS_SERVICE_NAME": "Klayers.github.invoke_pipeline",
            },
            layers=[deps_layer],
            description="Invoke multiple pipelines, one for each package",
        )
        fn_invoke_pipelines.add_to_role_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=[f"arn:aws:events:{region}:{account_id}:event-bus/default"],
            )
        )

        # 4. get_pr_number
        fn_get_pr_number = lambda_.Function(
            self,
            "GetPrNumberFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="get_pr_number.main",
            code=code,
            timeout=cdk.Duration.seconds(120),
            memory_size=256,
            log_group=logs.LogGroup(
                self,
                "GetPrNumberLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
            environment={
                **common_env,
                "POWERTOOLS_SERVICE_NAME": f"gh-push-{stage}",
            },
            layers=[deps_layer],
            description="Get PR Number from Github Event",
        )

        # 5. update_pr
        fn_update_pr = lambda_.Function(
            self,
            "UpdatePrFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="update_pr.main",
            code=code,
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
            log_group=logs.LogGroup(
                self,
                "UpdatePrLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
            environment={
                **common_env,
                "POWERTOOLS_SERVICE_NAME": f"gh-push-{stage}",
            },
            layers=[deps_layer],
            description="Update the PR with a comment on build status",
        )

        # 6. load_config
        fn_load_config = lambda_.Function(
            self,
            "LoadConfigFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="load_config.main",
            code=code,
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
            log_group=logs.LogGroup(
                self,
                "LoadConfigLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
            environment={
                **common_env,
                "POWERTOOLS_SERVICE_NAME": f"gh-push-{stage}",
            },
            layers=[deps_layer],
            description="Load New config into Dynamo",
        )
        fn_load_config.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:PutItem"],
                resources=[db_arn],
            )
        )
        fn_load_config.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{config_bucket_arn}/*"],
            )
        )
        fn_load_config.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:{region}:{account_id}:parameter/common-service/{stage}/*"],
            )
        )
        fn_load_config.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:Invoke"],
                resources=[f"arn:aws:execute-api:{region}:{account_id}:*/*"],
            )
        )

        # ==========================================
        # Step Function: gh-push-pipeline
        # ==========================================

        # Fail state
        catch_all_fail = sfn.Fail(
            self,
            "CatchAllFail",
            error="Failure",
            cause="Unknown",
        )

        # Branch 1: CheckPythonVersion -> MapPythonVersions (CheckNewPackages) -> InvokePipelines
        task_check_python_version = tasks.LambdaInvoke(
            self,
            "CheckPythonVersion",
            lambda_function=fn_check_python_versions,
            payload_response_only=True,
            retry_on_service_exceptions=False,
        )
        task_check_python_version.add_retry(
            errors=["States.Timeout"],
            max_attempts=2,
            backoff_rate=30,
            interval=cdk.Duration.seconds(60),
        )
        task_check_python_version.add_catch(
            catch_all_fail,
            errors=["States.ALL"],
        )

        task_check_new_packages = tasks.LambdaInvoke(
            self,
            "CheckNewPackages",
            lambda_function=fn_check_new_packages,
            payload_response_only=True,
            retry_on_service_exceptions=False,
        )
        map_python_versions = sfn.Map(self, "MapPythonVersions")
        map_python_versions.item_processor(task_check_new_packages)

        task_invoke_pipelines = tasks.LambdaInvoke(
            self,
            "InvokePipelines",
            lambda_function=fn_invoke_pipelines,
            payload_response_only=True,
            retry_on_service_exceptions=False,
        )
        task_invoke_pipelines.add_retry(
            errors=["States.Timeout"],
            max_attempts=2,
            backoff_rate=30,
            interval=cdk.Duration.seconds(60),
        )
        task_invoke_pipelines.add_catch(
            catch_all_fail,
            errors=["States.ALL"],
        )

        branch_packages = task_check_python_version.next(map_python_versions).next(
            task_invoke_pipelines
        )

        # Branch 2: GetPRNumber
        task_get_pr_number = tasks.LambdaInvoke(
            self,
            "GetPRNumber",
            lambda_function=fn_get_pr_number,
            payload_response_only=True,
            retry_on_service_exceptions=False,
        )

        # Parallel state
        parallel_on_push = sfn.Parallel(self, "OnPushEvent")
        parallel_on_push.branch(branch_packages)
        parallel_on_push.branch(task_get_pr_number)

        # Trailing tasks: LoadConfig -> UpdatePR
        task_load_config = tasks.LambdaInvoke(
            self,
            "LoadConfig",
            lambda_function=fn_load_config,
            payload_response_only=True,
            retry_on_service_exceptions=False,
        )

        task_update_pr = tasks.LambdaInvoke(
            self,
            "UpdatePR",
            lambda_function=fn_update_pr,
            payload_response_only=True,
            retry_on_service_exceptions=False,
        )

        definition = parallel_on_push.next(task_load_config).next(task_update_pr)

        state_machine = sfn.StateMachine(
            self,
            "GhPushPipeline",
            state_machine_name="gh-push-pipeline",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            comment="Trigger build from Github",
        )

        # SSM parameter and output for pipeline ARN
        ssm.StringParameter(
            self,
            "PipelineArnParameter",
            parameter_name=f"/gh-push/{stage}/PipelineArn",
            string_value=state_machine.state_machine_arn,
            description="Arn of Pipeline step function",
        )

        cdk.CfnOutput(
            self,
            "PipelineArn",
            value=state_machine.state_machine_arn,
            description="The ARN of the example state machine",
        )


def main():
    app = cdk.App()

    stage = app.node.try_get_context("stage") or os.environ.get("AWS_STAGE", "Klayers-defaultp38")
    account_id = STAGE_ACCOUNTS.get(stage, "367660174341")

    tfvars_path = Path(__file__).parent.parent / "Terraform" / "terraform.tfvars.json"
    if tfvars_path.exists():
        with open(tfvars_path, "r") as f:
            tfvars = json.load(f)
        region = tfvars.get("aws_region", {}).get(stage, "us-east-2")
    else:
        region = os.environ.get("AWS_REGION", "us-east-2")

    stack_name = f"klayers-gh-push-{stage}"
    GhPushStack(
        app,
        stack_name,
        stage=stage,
        env=cdk.Environment(account=account_id, region=region),
    )

    app.synth()


if __name__ == "__main__":
    main()
