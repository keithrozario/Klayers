import boto3
from boto3.dynamodb.conditions import Key


session = boto3.Session(profile_name='KlayersDefault')
dynamodb = session.resource("dynamodb")
table = dynamodb.Table("kl.Klayers-defaultp38.db-ver2")

region = "ap-southeast-1"
package = "requests"
python_version = "p3.9"

pk = f"lyr#{region}:{package}:{python_version}"

kwargs = {
    "KeyConditionExpression": Key("pk").eq(pk),
    "FilterExpression": "attribute_exists(dplySts)",  # don't get latest version
}

response = table.query(**kwargs)
for package in response['Items']:
    print(f"{package['dplySts']}: {package['pckgVrsn']}")