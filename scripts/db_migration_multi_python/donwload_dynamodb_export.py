import boto3
import gzip
import json
import os
import datetime
import time

# profile = "KlayersProdP38"
profile = 'KlayersDev'

# config = {"table_name": "kl.Klayers-prodp38.db", "region": "us-east-2"}
# config = {'table_name': 'kl.Klayers-devp38.db', 'region': 'us-west-2'}
config = {'bucket': 'klayers-bucket-defaultp38','table_name': 'kl.Klayers-defaultp38.db', 'region': 'ap-southeast-1'}
session = boto3.session.Session(profile_name=profile, region_name=config["region"])


def export_to_s3(client_token: str) -> str:

    dynamo_client = session.client('dynamodb')
    table_arn = dynamo_client.describe_table(TableName=config['table_name'])['Table']['TableArn']
    s3_prefix = f'AWSDynamoDBBackups/{client_token}/data'

    export_in_progress = True
    print(f"Initiating export for: {table_arn}")
    while export_in_progress:
        response = dynamo_client.export_table_to_point_in_time(
            TableArn=table_arn,
            ClientToken=client_token,
            S3Bucket=config['bucket'],
            S3Prefix=s3_prefix,
            ExportFormat='DYNAMODB_JSON',
        )
        export_in_progress = (response.get('ExportDescription').get('ExportStatus') == 'IN_PROGRESS')
        print(f"Export in progress: {export_in_progress}")
        time.sleep(10)

    return s3_prefix


def download_objects_from_s3(s3_prefix: str):

    print(f"Export complete, downloading files from S3")
    client = session.client('s3')

    response = client.list_objects_v2(
        Bucket=config['bucket'],
        Prefix=s3_prefix,
    )

    gz_files = [file for file in response['Contents'] if file['Key'][-3:] == ".gz"]

    for k, file in enumerate(gz_files):
        print(f"Downloading: {file['Key']}")
        if file['Key'][-3:] == ".gz":
            download_gz_file = f'./downloads/dynamo_download_{k}.gz'
            json_file = f'./downloads/dynamo_download_{k}.json'

            with open(download_gz_file, 'wb') as data:
                client.download_fileobj(config['bucket'], file['Key'], data)

            with gzip.open(download_gz_file, 'rb') as f:
                file_content = f.read()

            with open(json_file, 'wb') as output_file:
                output_file.write(file_content)
            os.remove(download_gz_file)
            print(f"Saved output to {json_file}")


def modify_data(input_file: str, output_file: str):

    with open(input_file, 'r') as ddb_backup_file:
        new_items = list()

        for k, line in enumerate(ddb_backup_file):
            item_container = json.loads(line)
            item = item_container['Item']
            if item['pk']['S'][:4] == 'lyr#':
                new_pk = f"{item['pk']['S'].replace('.', ':')}:p3.8"
                item['pk']['S'] = new_pk
                try:
                    if item['sk']['S'] != 'lyrVrsn0#':
                        item['rgn#PyVrsn'] = {"S": f"{item['rgn']['S']}#p3.8"}
                        item['pckg#PyVrsn'] = {"S": f"{item['pckg']['S']}#p3.8"}
                except KeyError:
                    print("error")
            elif item['pk']['S'] == 'bldVrsn0#':
                new_pk = f"{item['pk']['S']}p3.8"
                item['pk']['S'] = new_pk
                pass
            elif item['pk']['S'][:5] == 'bld#v':
                new_pk = f"{item['pk']['S']}:p3.8"
                item['pk']['S'] = new_pk
                pass
            else:
                print(f"Unknown: {item}")

            item['pyVrsn'] = {"S": "p3.8"}
            new_items.append(item)

    with open(output_file, 'w') as output:
        for item in new_items:
            output.write(json.dumps(item))
            output.write("\n")


if __name__ == "__main__":

    # client_token = datetime.datetime.now().isoformat()
    # s3_prefix = export_to_s3(client_token=client_token)
    # download_objects_from_s3(s3_prefix=s3_prefix)

    downloaded_jsons = os.listdir("downloads")

    for k, json_file in enumerate(downloaded_jsons):
        modify_data(input_file=f"./downloads/{json_file}", output_file=f"./output/{k}.json")