import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from infra import KlayersApiStack


def test_infra_stack_prod():
    app = cdk.App()
    stack = KlayersApiStack(
        app,
        "TestApiStackProd",
        stage="Klayers-prodp38",
        region="us-east-2",
        env=cdk.Environment(account="770693421928", region="us-east-2"),
    )
    template = Template.from_stack(stack)

    # Assert 4 Lambda functions on python3.13 and arm64
    py313_arm64_functions = template.find_resources(
        "AWS::Lambda::Function",
        {
            "Properties": {
                "Runtime": "python3.13",
                "Architectures": ["arm64"],
            }
        },
    )
    assert len(py313_arm64_functions) == 4
    for fn in py313_arm64_functions.values():
        props = fn["Properties"]
        assert props["MemorySize"] == 256
        assert props["Timeout"] == 10
        assert (
            props["Environment"]["Variables"]["POWERTOOLS_SERVICE_NAME"]
            == "Klayers.api"
        )

    # 1 Dependencies Layer
    template.resource_count_is("AWS::Lambda::LayerVersion", 1)
    template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {
            "CompatibleArchitectures": ["arm64"],
            "CompatibleRuntimes": ["python3.13"],
        },
    )

    # 1 ApiGatewayV2 HttpApi
    template.resource_count_is("AWS::ApiGatewayV2::Api", 1)

    # 8 Routes
    template.resource_count_is("AWS::ApiGatewayV2::Route", 8)
    expected_routes = [
        "GET /api/v1/layers/latest/{region}/{package}",
        "GET /api/v1/layers/latest/{region}",
        "GET /api/v2/{python_version}/layers/latest/{region}",
        "GET /api/v2/{python_version}/layers/latest/{region}/{format}",
        "GET /api/v1/layers/{region}/{package}",
        "GET /api/v2/{python_version}/layers/{region}/{package}",
        "GET /api/v1/builds/latest",
        "GET /api/v2/{python_version}/builds/latest",
    ]
    for route in expected_routes:
        template.has_resource_properties(
            "AWS::ApiGatewayV2::Route",
            {"RouteKey": route},
        )

    # 1 CloudFront Distribution
    template.resource_count_is("AWS::CloudFront::Distribution", 1)
    template.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": Match.object_like(
                {
                    "HttpVersion": "http2",
                    "PriceClass": "PriceClass_All",
                    "ViewerCertificate": Match.object_like(
                        {
                            "MinimumProtocolVersion": "TLSv1.2_2019",
                            "SslSupportMethod": "sni-only",
                        }
                    ),
                    "DefaultCacheBehavior": Match.object_like(
                        {
                            "AllowedMethods": ["GET", "HEAD"],
                            "CachedMethods": ["GET", "HEAD"],
                            "Compress": True,
                            "DefaultTTL": 3600,
                            "MaxTTL": 86400,
                            "MinTTL": 3600,
                            "ViewerProtocolPolicy": "https-only",
                        }
                    ),
                }
            )
        },
    )

    # 1 SSM Parameter for cfDistribution id
    template.has_resource_properties(
        "AWS::SSM::Parameter",
        {
            "Name": "/kl/Klayers-prodp38/api/cfDistribution/id",
            "Type": "String",
        },
    )


def test_infra_stack_default():
    app = cdk.App()
    stack = KlayersApiStack(
        app,
        "TestApiStackDefault",
        stage="Klayers-defaultp38",
        region="ap-southeast-1",
        env=cdk.Environment(account="367660174341", region="ap-southeast-1"),
    )
    template = Template.from_stack(stack)
    py313_arm64_functions = template.find_resources(
        "AWS::Lambda::Function",
        {
            "Properties": {
                "Runtime": "python3.13",
                "Architectures": ["arm64"],
            }
        },
    )
    assert len(py313_arm64_functions) == 4
    template.has_resource_properties(
        "AWS::SSM::Parameter",
        {
            "Name": "/kl/Klayers-defaultp38/api/cfDistribution/id",
            "Type": "String",
        },
    )
