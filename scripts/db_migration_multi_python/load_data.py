import boto3
import json


def map_item(dynamo_item: str) -> dict:
    """
    Args:
        dynamo_item: Dictonary of item in raw DynamoDB format ( e.g key: {'S': <value>}
    Returns:
        mapped_item : Dict of item in naive format (e.g. key: value)
    """

    mapped_item = {}
    temp_item = json.loads(dynamo_item)
    for key in temp_item.keys():
        if 'S' in temp_item[key].keys():
            mapped_item[key] = str(temp_item[key]['S'])
        elif 'N' in temp_item[key].keys():
            mapped_item[key] = int(temp_item[key]['N'])

    return mapped_item


# profile = "KlayersProdP38"
profile = 'KlayersDev'

# config = {"table_name": "kl.Klayers-prodp38.db", "region": "us-east-2"}
# config = {'table_name': 'kl.Klayers-devp38.db', 'region': 'us-west-2'}
config = {'table_name': 'kl.Klayers-defaultp38.db-ver2', 'region': 'ap-southeast-1'}


session = boto3.session.Session(profile_name=profile, region_name=config["region"])
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(config["table_name"])


with open("output.json", "r") as input_file:
    items = input_file.readlines()

with table.batch_writer() as batch:
    for k, item in enumerate(items):
        new_item = map_item(item)
        batch.put_item(Item=new_item)
        if k % 10 == 0:
            print(f"Written {k}/{len(items)} to {config['table_name']}")
