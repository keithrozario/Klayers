import json
import os
import shutil
import subprocess
from pathlib import Path

import aws_cdk as cdk
import constructs
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_apigatewayv2 as apigwv2,
)
from aws_cdk import (
    aws_apigatewayv2_integrations as apigwv2_integrations,
)
from aws_cdk import (
    aws_cloudfront as cloudfront,
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

STAGE_ACCOUNTS = {
    "Klayers-defaultp38": "367660174341",
    "Klayers-devp38": "908645878701",
    "Klayers-prodp38": "770693421928",
}


def build_deps_layer(scope: constructs.Construct) -> lambda_.LayerVersion:
    """Builds and packages requirements.txt for arm64 Python 3.13 into a Lambda Layer."""
    app_dir = Path(__file__).parent.resolve()
    layer_dir = app_dir / ".layer_build"
    target_dir = layer_dir / "python"
    req_file = app_dir / "requirements.txt"
    marker_file = target_dir / ".installed"

    should_build = True
    if (
        marker_file.exists()
        and req_file.exists()
        and marker_file.stat().st_mtime >= req_file.stat().st_mtime
    ):
        should_build = False

    if should_build:
        target_dir.mkdir(parents=True, exist_ok=True)
        uv_cmd = shutil.which("uv") or "uv"
        subprocess.run(
            [
                uv_cmd,
                "pip",
                "install",
                "--quiet",
                "--python-platform",
                "aarch64-manylinux2014",
                "--python-version",
                "3.13",
                "--target",
                str(target_dir),
                "-r",
                str(req_file),
            ],
            check=True,
        )
        marker_file.touch()

    return lambda_.LayerVersion(
        scope,
        "ApiDepsLayer",
        code=lambda_.Code.from_asset(str(layer_dir)),
        compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
        compatible_architectures=[lambda_.Architecture.ARM_64],
        description="Dependencies layer for Klayers API (powertools, tabulate)",
    )


class KlayersApiStack(Stack):
    def __init__(
        self,
        scope: constructs.Construct,
        construct_id: str,
        stage: str,
        region: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.stage = stage

        # Resolve SSM parameters
        layers_bucket_name = ssm.StringParameter.value_for_string_parameter(
            self, f"/kl/{stage}/layers_bucket/name"
        )
        db_name = ssm.StringParameter.value_for_string_parameter(
            self, f"/kl/{stage}/db-ver2/name"
        )
        db_arn = ssm.StringParameter.value_for_string_parameter(
            self, f"/kl/{stage}/db-ver2/arn"
        )
        api_cert_arn = ssm.StringParameter.value_for_string_parameter(
            self, f"/kl/{stage}/api/cert/arn"
        )
        api_domain_name = ssm.StringParameter.value_for_string_parameter(
            self, f"/kl/{stage}/api/domain_name"
        )

        # Build runtime dependencies layer
        deps_layer = build_deps_layer(self)

        src_dir = str(Path(__file__).parent.resolve() / "src")
        common_env = {
            "STAGE": stage,
            "LOG_LEVEL": "INFO",
            "DB_NAME": db_name,
            "BUCKET_NAME": layers_bucket_name,
            "POWERTOOLS_SERVICE_NAME": "Klayers.api",
        }

        # 1. arn_by_package_region
        fn_arn_by_package_region = lambda_.Function(
            self,
            "ArnByPackageRegionFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            architecture=lambda_.Architecture.ARM_64,
            handler="layers.latest_region_package.main",
            code=lambda_.Code.from_asset(src_dir),
            memory_size=256,
            timeout=Duration.seconds(10),
            log_group=logs.LogGroup(
                self,
                "ArnByPackageRegionLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=RemovalPolicy.DESTROY,
            ),
            environment=common_env,
            layers=[deps_layer],
            description="Get latest layer per package per region",
        )
        fn_arn_by_package_region.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem"],
                resources=[db_arn],
            )
        )

        # 2. arn_by_regions
        fn_arn_by_regions = lambda_.Function(
            self,
            "ArnByRegionsFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            architecture=lambda_.Architecture.ARM_64,
            handler="layers.latest_region.main",
            code=lambda_.Code.from_asset(src_dir),
            memory_size=256,
            timeout=Duration.seconds(10),
            log_group=logs.LogGroup(
                self,
                "ArnByRegionsLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=RemovalPolicy.DESTROY,
            ),
            environment=common_env,
            layers=[deps_layer],
            description="Get latest packages per region",
        )
        fn_arn_by_regions.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Query"],
                resources=[f"{db_arn}/index/deployed_in_region_by_python_version"],
            )
        )

        # 3. list_layers
        fn_list_layers = lambda_.Function(
            self,
            "ListLayersFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            architecture=lambda_.Architecture.ARM_64,
            handler="layers.list_layer_version.main",
            code=lambda_.Code.from_asset(src_dir),
            memory_size=256,
            timeout=Duration.seconds(10),
            log_group=logs.LogGroup(
                self,
                "ListLayersLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=RemovalPolicy.DESTROY,
            ),
            environment=common_env,
            layers=[deps_layer],
            description="List all layer versions in a region per package",
        )
        fn_list_layers.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Query"],
                resources=[db_arn],
            )
        )

        # 4. list_builds
        fn_list_builds = lambda_.Function(
            self,
            "ListBuildsFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            architecture=lambda_.Architecture.ARM_64,
            handler="builds.list_builds.main",
            code=lambda_.Code.from_asset(src_dir),
            memory_size=256,
            timeout=Duration.seconds(10),
            log_group=logs.LogGroup(
                self,
                "ListBuildsLogGroup",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=RemovalPolicy.DESTROY,
            ),
            environment=common_env,
            layers=[deps_layer],
            description="Get latest builds",
        )
        fn_list_builds.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Query"],
                resources=[db_arn],
            )
        )

        # HTTP API (ApiGatewayV2)
        http_api = apigwv2.HttpApi(
            self,
            "HttpApi",
            api_name=f"{stage}-api",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_headers=["*"],
                allow_methods=[apigwv2.CorsHttpMethod.ANY],
                allow_origins=["*"],
            ),
        )

        integration_arn_by_package_region = apigwv2_integrations.HttpLambdaIntegration(
            "ArnByPackageRegionIntegration", fn_arn_by_package_region
        )
        integration_arn_by_regions = apigwv2_integrations.HttpLambdaIntegration(
            "ArnByRegionsIntegration", fn_arn_by_regions
        )
        integration_list_layers = apigwv2_integrations.HttpLambdaIntegration(
            "ListLayersIntegration", fn_list_layers
        )
        integration_list_builds = apigwv2_integrations.HttpLambdaIntegration(
            "ListBuildsIntegration", fn_list_builds
        )

        # 8 Routes across layers and builds
        http_api.add_routes(
            path="/api/v1/layers/latest/{region}/{package}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration_arn_by_package_region,
        )
        http_api.add_routes(
            path="/api/v1/layers/latest/{region}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration_arn_by_regions,
        )
        http_api.add_routes(
            path="/api/v2/{python_version}/layers/latest/{region}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration_arn_by_regions,
        )
        http_api.add_routes(
            path="/api/v2/{python_version}/layers/latest/{region}/{format}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration_arn_by_regions,
        )
        http_api.add_routes(
            path="/api/v1/layers/{region}/{package}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration_list_layers,
        )
        http_api.add_routes(
            path="/api/v2/{python_version}/layers/{region}/{package}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration_list_layers,
        )
        http_api.add_routes(
            path="/api/v1/builds/latest",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration_list_builds,
        )
        http_api.add_routes(
            path="/api/v2/{python_version}/builds/latest",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration_list_builds,
        )

        # CloudFront Distribution
        cfn_dist = cloudfront.CfnDistribution(
            self,
            "CloudFrontDistribution",
            distribution_config=cloudfront.CfnDistribution.DistributionConfigProperty(
                aliases=[api_domain_name],
                enabled=True,
                http_version="http2",
                price_class="PriceClass_All",
                viewer_certificate=cloudfront.CfnDistribution.ViewerCertificateProperty(
                    acm_certificate_arn=api_cert_arn,
                    minimum_protocol_version="TLSv1.2_2019",
                    ssl_support_method="sni-only",
                ),
                origins=[
                    cloudfront.CfnDistribution.OriginProperty(
                        id=stage,
                        domain_name=f"{http_api.api_id}.execute-api.{region}.amazonaws.com",
                        custom_origin_config=cloudfront.CfnDistribution.CustomOriginConfigProperty(
                            http_port=80,
                            https_port=443,
                            origin_protocol_policy="https-only",
                            origin_ssl_protocols=["TLSv1.2"],
                        ),
                    ),
                ],
                default_cache_behavior=cloudfront.CfnDistribution.DefaultCacheBehaviorProperty(
                    allowed_methods=["GET", "HEAD"],
                    cached_methods=["GET", "HEAD"],
                    target_origin_id=stage,
                    forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                        query_string=True,
                        cookies=cloudfront.CfnDistribution.CookiesProperty(
                            forward="none"
                        ),
                    ),
                    min_ttl=3600,
                    default_ttl=3600,
                    max_ttl=86400,
                    viewer_protocol_policy="https-only",
                    compress=True,
                ),
            ),
        )

        # Distribution ID in SSM Parameter
        ssm.StringParameter(
            self,
            "DistributionSSM",
            parameter_name=f"/kl/{stage}/api/cfDistribution/id",
            string_value=cfn_dist.ref,
            description="Cloudfront Distribution ID for API",
            tier=ssm.ParameterTier.STANDARD,
        )


def main():
    app = cdk.App()
    stage = app.node.try_get_context("stage") or os.environ.get(
        "AWS_STAGE", "Klayers-defaultp38"
    )

    tfvars_path = Path(__file__).parent.parent / "Terraform" / "terraform.tfvars.json"
    with open(tfvars_path, encoding="utf-8") as f:
        tf_vars = json.load(f)

    region = tf_vars.get("aws_region", {}).get(stage, "ap-southeast-1")
    account_id = STAGE_ACCOUNTS.get(stage, "367660174341")

    KlayersApiStack(
        app,
        f"klayers-api-{stage}",
        stage=stage,
        region=region,
        env=cdk.Environment(account=account_id, region=region),
    )

    app.synth()


if __name__ == "__main__":
    main()
