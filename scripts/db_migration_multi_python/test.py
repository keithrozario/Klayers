import boto3
import json

profile = "KlayersDev"

# config = {"table_name": "kl.Klayers-prodp38.db", "region": "us-east-2"}
# config = {'bucket': 'klayers-bucket--devp38',
#           'table_name_source': 'kl.Klayers-devp38.db',
#           'region': 'us-west-2',
#           'table_name_dest': 'kl.Klayers-devp38.db-ver2'}

config = {
    "bucket": "klayers-bucket-defaultp38",
    "table_name_source": "kl.Klayers-defaultp38.db",
    "table_name_dest": "kl.Klayers-defaultp38.db-ver2",
    "region": "ap-southeast-1",
}
session = boto3.session.Session(profile_name=profile, region_name=config["region"])
dynamo_client = session.resource("dynamodb")
table = dynamo_client.Table(config["table_name_dest"])
client = session.client("events")


for package in ["requests", "idna"]:
    for python_version in ["p3.8", "p3.9"]:
        entry = {
            "Source": "Klayers.invoke.Klayers-defaultp38",
            "Resources": [],
            "DetailType": "invoke_pipeline",
            "Detail": json.dumps(
                {
                    "package": package,
                    "python_version": python_version,
                    "force_deploy": True,
                    "force_build": True,
                }
            ),
            "EventBusName": "default",
        }
        _ = client.put_events(Entries=[entry])

# items = [
#     {'pk': 'bldVrsn0#p3.8', 'sk': 'pckg#idna'},
#     {'pk': 'bldVrsn0#p3.9', 'sk': 'pckg#idna'},
#     {'pk': 'lyr#ap-southeast-1:requests:p3.9', 'sk': 'lyrVrsn0#'},
#     {'pk': 'lyr#ap-southeast-1:requests:p3.9', 'sk': 'lyrVrsn#v1'},
#     {'pk': 'lyr#ap-southeast-1:requests:p3.8', 'sk': 'lyrVrsn0#'},
#     {'pk': 'lyr#ap-southeast-1:requests:p3.8', 'sk': 'lyrVrsn#v1'},
# ]
#
# for item in items:
#     response = table.update_item(
#         Key=item,
#         UpdateExpression="SET rqrmntsHsh = :dummy",
#         ExpressionAttributeValues={
#             ":dummy": '...'
#         }
#     )


# entries = []
# for package in ['requests', 'idna']:
#     for python_version in ['p3.8', 'p3.9']:
#         entry = {
#             "Source": "Klayers.invoke.Klayers-devp38",
#             "Resources": [],
#             "DetailType": "invoke_pipeline",
#             "Detail": json.dumps({"package": package, "python_version": python_version}),
#             "EventBusName": "default",
#         }
#         _ = client.put_events(Entries=[entry])
#
