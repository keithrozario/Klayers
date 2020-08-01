"""
Add the package fields to build items.
Derived from the sk field
"""


import boto3

from boto3.dynamodb.conditions import Key, Attr

profile = "KlayersProdP38"
# profile = 'KlayersDev'

config = {"table_name": "kl.Klayers-prodp38.db", "region": "us-east-2"}
# config = {'table_name': 'kl.Klayers-devp38.db', 'region': 'us-west-2'}
# config = {'table_name': 'kl.Klayers-defaultp38.db', 'region': 'ap-southeast-1'}

session = boto3.session.Session(profile_name=profile, region_name=config["region"])
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(config["table_name"])

kwargs = {
    "Select": "ALL_ATTRIBUTES",
    "FilterExpression": Attr("pk").begins_with("bld"),
    "ConsistentRead": False,
}

items = list()

while True:
    response = table.scan(**kwargs)
    items.extend(response["Items"])
    try:
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
    except KeyError:
        break

with table.batch_writer() as batch:
    for k, item in enumerate(items):
        item["pckg"] = item["sk"][5:]
        batch.put_item(Item=item)
        if k % 10 == 0:
            print(f"Written {k}/{len(items)} to {config['table_name']}")
