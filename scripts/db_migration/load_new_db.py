import boto3
from boto3.dynamodb.conditions import Attr

profile = "KlayersProdP38"
# profile = 'KlayersDev'

config = {"table_name": "kl.Klayers-prodp38.db", "region": "us-east-2"}
# config = {'table_name': 'kl.Klayers-devp38.db', 'region': 'us-west-2'}
# config = {'table_name': 'kl.Klayers-defaultp38.db', 'region': 'ap-southeast-1'}

session = boto3.session.Session(profile_name=profile, region_name=config["region"])
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(config["table_name"])


response = table.scan(
    Select="ALL_ATTRIBUTES",
    FilterExpression=Attr("pk").BEGINS_WITH("bld"),
    ConsistentRead=False,
)
