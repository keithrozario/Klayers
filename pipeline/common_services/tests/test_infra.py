import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from infra import CommonServicesStack


def test_common_services_infra_stack():
    app = cdk.App()
    stage = "Klayers-prodp38"
    stack = CommonServicesStack(
        app,
        f"klayers-common-{stage}",
        stage=stage,
        env=cdk.Environment(account="770693421928", region="us-east-2"),
    )
    template = Template.from_stack(stack)

    # 1. Assert exactly 4 Lambda functions with Python 3.13
    template.resource_count_is("AWS::Lambda::Function", 4)

    # Verify check_python_versions function properties
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "get_python_versions.main",
            "Runtime": "python3.13",
            "Timeout": 3,
            "MemorySize": 256,
            "Environment": {
                "Variables": {
                    "STAGE": stage,
                    "LOG_LEVEL": "INFO",
                    "POWERTOOLS_SERVICE_NAME": "Klayers.common-service",
                }
            },
        },
    )

    # Verify get_config function properties
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "get_config.main",
            "Runtime": "python3.13",
            "Timeout": 3,
            "MemorySize": 256,
        },
    )

    # Verify get_config_s3 function properties
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "get_config_s3.main",
            "Runtime": "python3.13",
            "Timeout": 3,
            "MemorySize": 256,
        },
    )

    # Verify load_config function properties
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "load_config_from_s3.main",
            "Runtime": "python3.13",
            "Timeout": 29,
            "MemorySize": 512,
        },
    )

    # 2. Assert HTTP API and 4 routes with AWS_IAM authorization
    template.resource_count_is("AWS::ApiGatewayV2::Api", 1)

    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {
            "RouteKey": "GET /api/v1/python-versions",
            "AuthorizationType": "AWS_IAM",
        },
    )

    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {
            "RouteKey": "GET /api/v1/config/{python_version}/{config_type}",
            "AuthorizationType": "AWS_IAM",
        },
    )

    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {
            "RouteKey": "GET /api/v1/configS3/{python_version}/{config_type}",
            "AuthorizationType": "AWS_IAM",
        },
    )

    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {
            "RouteKey": "POST /api/v1/load-config",
            "AuthorizationType": "AWS_IAM",
        },
    )

    # 3. Assert SSM Parameters matching serverless.yml
    template.has_resource_properties(
        "AWS::SSM::Parameter",
        {
            "Name": f"/common-service/{stage}/CommonServiceApi/URL",
            "Type": "String",
        },
    )

    template.has_resource_properties(
        "AWS::SSM::Parameter",
        {
            "Name": f"/common-service/{stage}/CommonServiceApi/arn",
            "Type": "String",
            "Value": {
                "Fn::Join": [
                    "",
                    Match.array_with(
                        [
                            "arn:aws:execute-api:us-east-2:770693421928:",
                            "/*",
                        ]
                    ),
                ]
            },
        },
    )

    # 4. Assert 90-day log retention LogGroups
    template.has_resource_properties(
        "AWS::Logs::LogGroup",
        {
            "RetentionInDays": 90,
        },
    )
