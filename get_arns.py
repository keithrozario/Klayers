#! /usr/bin/env python3
import boto3
import json

session = boto3.Session(profile_name='LayerUploader')

regions = ['ap-northeast-1', 'ap-northeast-2', 'ap-south-1',
           'ap-southeast-1', 'ap-southeast-2', 'ca-central-1',
           'eu-central-1', 'eu-north-1', 'eu-west-1',
           'eu-west-2', 'eu-west-3', 'sa-east-1',
           'us-east-1', 'us-east-2','us-west-1',
           'us-west-2']

output = dict()

for region in regions:
    client = session.client('lambda', region_name=region)
    output[region] = dict()
    # every version of every layer
    for layer in client.list_layers()['Layers']:
        output[region][layer['LayerName']] = []
        for version in client.list_layer_versions(LayerName=layer['LayerName'])['LayerVersions']:
            output[region][layer['LayerName']].append(version['LayerVersionArn'])
            print("{}: {}".format(region, version['LayerVersionArn']))

with open('arns.json', 'w') as f:
    f.write(json.dumps(output, indent=4, sort_keys=True))
