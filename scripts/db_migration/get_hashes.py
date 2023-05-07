import boto3
import json

config = {"table_name": "klayers-requirements-prod", "region": "us-east-2"}
profile = "KlayersProdP38"


def scan_table(table_name, client):
    kwargs = {"TableName": table_name, "Select": "ALL_ATTRIBUTES"}
    items = []

    while True:
        response = client.scan(**kwargs)
        items.extend(response["Items"])

        try:
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        except KeyError:
            break

    return items


session = boto3.session.Session(profile_name=profile, region_name=config["region"])
client = session.client("dynamodb")
items = scan_table(config["table_name"], client)

with open("hashes.json", "r") as hash_file:
    hashes = json.loads(hash_file.read())

for item in items:
    hashes[item["requirements_hash"]["S"]] = item["requirements"]["S"]

print(len(hashes.keys()))
