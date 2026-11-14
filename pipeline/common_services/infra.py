"""CDK Mini-App for Klayers Common Services.

Deploys:
  - 4 Python 3.13 Lambda functions for configuration management
  - HTTP API (API Gateway v2) with AWS_IAM default authorization
  - SSM Parameters for CommonServiceApi URL and ARN
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import aws_cdk as cdk
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_apigatewayv2_authorizers import HttpIamAuthorizer
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct

STAGE_ACCOUNTS = {
    "Klayers-defaultp38": "367660174341",
    "Klayers-devp38": "908645878701",
    "Klayers-prodp38": "770693421928",
}


def build_deps_layer(scope: Construct) -> lambda_.LayerVersion:
    """Build a self-contained Lambda layer using uv pip install."""
    project_dir = Path(__file__).resolve().parent
    layer_dir = project_dir / ".layer_build"
    target_python_dir = layer_dir / "python"
    requirements_txt = project_dir / "requirements.txt"

    marker_file = target_python_dir / ".installed"
    should_build = True
    if (
        marker_file.exists()
        and requirements_txt.exists()
        and marker_file.stat().st_mtime >= requirements_txt.stat().st_mtime
    ):
        should_build = False

    if should_build:
        target_python_dir.mkdir(parents=True, exist_ok=True)
        uv_cmd = shutil.which("uv") or "uv"
        subprocess.run(
            [
                uv_cmd,
                "pip",
                "install",
                "--quiet",
                "--python-platform",
                "x86_64-manylinux2014",
                "--python-version",
                "3.13",
                "--target",
                str(target_python_dir),
                "-r",
                str(requirements_txt),
            ],
            check=True,
        )
        marker_file.touch()

    return lambda_.LayerVersion(
        scope,
        "CommonDepsLayer",
        code=lambda_.Code.from_asset(str(layer_dir)),
        compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
        description="Self-contained dependencies layer for common services",
    )


class CommonServicesStack(cdk.Stack):
    """CDK Stack for Klayers Common Services."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stage: str = "Klayers-defaultp38",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.stage = stage

        # Resolve DynamoDB and S3 bucket details from SSM
        db_arn = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/db-ver2/arn")
        db_name = ssm.StringParameter.value_for_string_parameter(self, f"/kl/{stage}/db-ver2/name")
        config_bucket_arn = ssm.StringParameter.value_for_string_parameter(
            self, f"/kl/{stage}/config_bucket/arn"
        )
        config_bucket_name = ssm.StringParameter.value_for_string_parameter(
            self, f"/kl/{stage}/config_bucket/name"
        )

        # Build self-contained dependency layer
        deps_layer = build_deps_layer(self)

        src_dir = Path(__file__).resolve().parent / "src"

        common_env = {
            "STAGE": stage,
            "LOG_LEVEL": "INFO",
            "DB_NAME": db_name,
            "CONFIG_BUCKET": config_bucket_name,
            "POWERTOOLS_SERVICE_NAME": "Klayers.common-service",
        }

        # 1. check_python_versions Lambda Function
        check_python_versions = lambda_.Function(
            self,
            "CheckPythonVersionsFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="get_python_versions.main",
            code=lambda_.Code.from_asset(str(src_dir)),
            layers=[deps_layer],
            timeout=cdk.Duration.seconds(3),
            memory_size=256,
            environment=common_env,
            log_group=logs.LogGroup(
                self,
                "CheckPythonVersionsLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
            description="Returns python versions currently supported",
        )
        check_python_versions.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem"],
                resources=[db_arn],
            )
        )

        # 2. get_config Lambda Function
        get_config = lambda_.Function(
            self,
            "GetConfigFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="get_config.main",
            code=lambda_.Code.from_asset(str(src_dir)),
            layers=[deps_layer],
            timeout=cdk.Duration.seconds(3),
            memory_size=256,
            environment=common_env,
            log_group=logs.LogGroup(
                self,
                "GetConfigLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
            description="Compares python versions",
        )
        get_config.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem"],
                resources=[db_arn],
            )
        )

        # 3. get_config_s3 Lambda Function
        get_config_s3 = lambda_.Function(
            self,
            "GetConfigS3Function",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="get_config_s3.main",
            code=lambda_.Code.from_asset(str(src_dir)),
            layers=[deps_layer],
            timeout=cdk.Duration.seconds(3),
            memory_size=256,
            environment=common_env,
            log_group=logs.LogGroup(
                self,
                "GetConfigS3LogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
            description="Compares python versions",
        )
        get_config_s3.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{config_bucket_arn}/*"],
            )
        )

        # 4. load_config Lambda Function
        load_config = lambda_.Function(
            self,
            "LoadConfigFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="load_config_from_s3.main",
            code=lambda_.Code.from_asset(str(src_dir)),
            layers=[deps_layer],
            timeout=cdk.Duration.seconds(29),
            memory_size=512,
            environment=common_env,
            log_group=logs.LogGroup(
                self,
                "LoadConfigLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
            description="Load New config from S3 into Dynamo",
        )
        load_config.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:PutItem"],
                resources=[db_arn],
            )
        )
        load_config.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{config_bucket_arn}/*"],
            )
        )

        # HTTP API with AWS_IAM default authorization
        http_api = apigwv2.HttpApi(
            self,
            "CommonServiceApi",
            default_authorizer=HttpIamAuthorizer(),
            description=f"Common Service API for {stage}",
        )

        # Add routes
        http_api.add_routes(
            path="/api/v1/python-versions",
            methods=[apigwv2.HttpMethod.GET],
            integration=HttpLambdaIntegration(
                "CheckPythonVersionsIntegration", check_python_versions
            ),
        )

        http_api.add_routes(
            path="/api/v1/config/{python_version}/{config_type}",
            methods=[apigwv2.HttpMethod.GET],
            integration=HttpLambdaIntegration("GetConfigIntegration", get_config),
        )

        http_api.add_routes(
            path="/api/v1/configS3/{python_version}/{config_type}",
            methods=[apigwv2.HttpMethod.GET],
            integration=HttpLambdaIntegration("GetConfigS3Integration", get_config_s3),
        )

        http_api.add_routes(
            path="/api/v1/load-config",
            methods=[apigwv2.HttpMethod.POST],
            integration=HttpLambdaIntegration("LoadConfigIntegration", load_config),
        )

        # SSM Parameters matching serverless.yml (service was 'common-service')
        self.api_url_param = ssm.StringParameter(
            self,
            "CommonServiceApiUrlParam",
            parameter_name=f"/common-service/{stage}/CommonServiceApi/URL",
            string_value=http_api.api_endpoint,
            description="URL for Common Service API",
        )

        arn_value = f"arn:aws:execute-api:{self.region}:{self.account}:{http_api.api_id}/*"
        self.api_arn_param = ssm.StringParameter(
            self,
            "CommonServiceApiArnParam",
            parameter_name=f"/common-service/{stage}/CommonServiceApi/arn",
            string_value=arn_value,
            description="Arn for Common Service API",
        )


def main() -> None:
    app = cdk.App()
    stage = app.node.try_get_context("stage") or os.environ.get("AWS_STAGE", "Klayers-defaultp38")

    tfvars_path = Path(__file__).resolve().parent.parent / "Terraform" / "terraform.tfvars.json"
    if tfvars_path.exists():
        with open(tfvars_path) as f:
            tfvars = json.load(f)
        region = tfvars.get("aws_region", {}).get(stage, "ap-southeast-1")
    else:
        region = os.environ.get("AWS_REGION", "ap-southeast-1")

    account = STAGE_ACCOUNTS.get(stage, os.environ.get("CDK_DEFAULT_ACCOUNT", "367660174341"))

    env = cdk.Environment(account=account, region=region)
    stack_name = f"klayers-common-{stage}"

    CommonServicesStack(app, stack_name, stage=stage, env=env)
    app.synth()


if __name__ == "__main__":
    main()
