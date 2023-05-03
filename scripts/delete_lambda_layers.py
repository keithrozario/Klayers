import boto3


def get_aws_regions():
    """
    returns:
        aws_regions : List of all regions to deploy lambdas into
    """

    aws_regions = [
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-south-1",
        "ap-southeast-1",
        "ap-southeast-2",
        "ca-central-1",
        "eu-central-1",
        "eu-north-1",
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "sa-east-1",
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
    ]

    return aws_regions


if __name__ == "__main__":
    boto3.setup_default_session(profile_name="LayerUploader")
    regions = get_aws_regions()

    for region in regions:
        client = boto3.client("lambda", region_name=region)

        kwargs = {}
        layers = []
        while True:
            response = client.list_layers(**kwargs)
            layers.extend(response["Layers"])
            kwargs["Marker"] = response.get("NextMarker", False)
            if not kwargs["Marker"]:
                break

        for layer in layers:
            if layer["LayerName"].find("default") > -1:
                response = client.list_layer_versions(LayerName=layer["LayerName"])
                for version in response["LayerVersions"]:
                    layer_version = version["LayerVersionArn"].split(":")[-1]
                    client.delete_layer_version(
                        LayerName=layer["LayerName"], VersionNumber=int(layer_version)
                    )
            else:
                print(f"Keeping layer: {layer['LayerName']}")
