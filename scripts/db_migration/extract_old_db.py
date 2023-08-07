import boto3
import json
import copy


# config = {'table_name': 'klayers-versions-dev', 'region': 'us-west-2'}
# config = {'table_name': 'klayers-versions', 'region': 'ap-southeast-1'}
config = {"table_name": "klayers-versions-prod", "region": "us-east-2"}
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

version_items = scan_table(
    table_name=config["table_name"],
    client=client,
)

with open("hashes.json", "r") as hash_file:
    hashes = json.loads(hash_file.read())

new_items = list()

for k, item in enumerate(version_items):
    new_item = {
        "pk": f"lyr#{item['deployed_region']['S']}.{item['package']['S']}",
        "sk": f"lyrVrsn#v{item['layer_version']['N']}",
        "rgnPckg": f"{item['deployed_region']['S']}.{item['package']['S']}",
        "pckg": f"{item['package']['S']}",
        "arn": item["layer_version_arn"]["S"],
        "lyrVrsn": int(item["layer_version"]["N"]),
        "pckgVrsn": item["package_version"]["S"],
        "rqrmntsHsh": item["requirements_hash"]["S"],
        "rgn": item["deployed_region"]["S"],
        "crtdDt": f"{item['created_date']['S'][:-5]}000",
    }

    try:
        new_item["rqrmntsTxt"] = hashes[item["requirements_hash"]["S"]]
    except KeyError:
        pass

    # Is this the latest version?
    if "time_to_live" in item.keys():
        new_item["dplySts"] = "deprecated"
        new_item["exDt"] = int(item["time_to_live"]["N"])
    else:
        v0_item = copy.deepcopy(new_item)
        v0_item["sk"] = "lyrVrsn0#"
        new_items.append(v0_item)
        new_item["dplySts"] = "latest"

    new_items.append(new_item)


sorted_items = sorted(new_items, key=lambda i: (i["pk"], i["sk"]))

with open("output.json", "w") as output_file:
    for item in sorted_items:
        output_file.write(f"{json.dumps(item)}\n")
