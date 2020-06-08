import boto3
import json

profile = 'KlayersProdP38'
# profile = 'KlayersDev'

config = {'table_name': 'kl.Klayers-prodp38.db', 'region': 'us-east-2'}
# config = {'table_name': 'kl.Klayers-devp38.db', 'region': 'us-west-2'}
# config = {'table_name': 'kl.Klayers-defaultp38.db', 'region': 'ap-southeast-1'}

session = boto3.session.Session(profile_name=profile, region_name=config['region'])
dynamodb = session.resource('dynamodb')
table = dynamodb.Table(config['table_name'])

items = list()
with open('output.json', 'r') as migration_file:
    for line in migration_file.readlines():
        items.append(json.loads(line))

with table.batch_writer() as batch:
    for k, item in enumerate(items):
        batch.put_item(Item=item)
        if k % 10 == 0:
            print(f"Written {k}/{len(items)} to {config['table_name']}")

print("Done")