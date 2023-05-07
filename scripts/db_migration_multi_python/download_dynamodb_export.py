import boto3
import gzip
import json
import os
import shutil
import datetime
import time

profile = "KlayersProdP38"
# profile = 'KlayersDev'

# config = {"table_name": "kl.Klayers-prodp38.db", "region": "us-east-2"}
# config = {'bucket': 'klayers-bucket--devp38',
#           'table_name_source': 'kl.Klayers-devp38.db',
#           'region': 'us-west-2',
#           'table_name_dest': 'kl.Klayers-devp38.db-ver2'}

# config = {'bucket': 'klayers-bucket-defaultp38',
#           'table_name_source': 'kl.Klayers-defaultp38.db',
#           'table_name_dest': 'kl.Klayers-defaultp38.db-ver2',
#           'region': 'ap-southeast-1'}

config = {
    "bucket": "klayers-bucket--prodp38",
    "table_name_source": "kl.Klayers-prodp38.db",
    "table_name_dest": "kl.Klayers-prodp38.db-ver2",
    "region": "us-east-2",
}

session = boto3.session.Session(profile_name=profile, region_name=config["region"])
error_file = "error_items.jsonl"


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
        if "S" in temp_item[key].keys():
            mapped_item[key] = str(temp_item[key]["S"])
        elif "N" in temp_item[key].keys():
            mapped_item[key] = int(temp_item[key]["N"])

    return mapped_item


def load_data(items: list) -> None:
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table(config["table_name_dest"])

    with table.batch_writer() as batch:
        for k, item in enumerate(items):
            new_item = map_item(item)
            batch.put_item(Item=new_item)
            if k % 100 == 0:
                print(f"Written {k}/{len(items)} to {config['table_name_dest']}")

    print(f"Exported {k} rows to {config['table_name_dest']}")
    return None


def export_to_s3(client_token: str) -> str:
    dynamo_client = session.client("dynamodb")
    table_arn = dynamo_client.describe_table(TableName=config["table_name_source"])[
        "Table"
    ]["TableArn"]
    s3_prefix = f"AWSDynamoDBBackups/{client_token}/data"

    export_in_progress = True
    print(f"Initiating export for: {table_arn}")
    while export_in_progress:
        response = dynamo_client.export_table_to_point_in_time(
            TableArn=table_arn,
            ClientToken=client_token,
            S3Bucket=config["bucket"],
            S3Prefix=s3_prefix,
            ExportFormat="DYNAMODB_JSON",
        )
        export_in_progress = (
            response.get("ExportDescription").get("ExportStatus") == "IN_PROGRESS"
        )
        print(f"Export in progress: {export_in_progress}")
        time.sleep(10)

    return s3_prefix


def download_objects_from_s3(s3_prefix: str):
    print(f"Export complete, downloading files from S3")
    client = session.client("s3")

    response = client.list_objects_v2(
        Bucket=config["bucket"],
        Prefix=s3_prefix,
    )

    gz_files = [file for file in response["Contents"] if file["Key"][-3:] == ".gz"]

    for k, file in enumerate(gz_files):
        print(f"Downloading: {file['Key']}")
        if file["Key"][-3:] == ".gz":
            download_gz_file = f"./downloads/dynamo_download_{k}.gz"
            json_file = f"./downloads/dynamo_download_{k}.json"

            with open(download_gz_file, "wb") as data:
                client.download_fileobj(config["bucket"], file["Key"], data)

            with gzip.open(download_gz_file, "rb") as f:
                file_content = f.read()

            with open(json_file, "wb") as output_file:
                output_file.write(file_content)
            os.remove(download_gz_file)
            print(f"Saved output to {json_file}")


def write_error_to_file(error_item: dict):
    with open(error_file, "a") as output:
        output.write(json.dumps(error_item))
        output.write("\n")


def modify_data(input_file: str, output_file: str):
    with open(input_file, "r") as ddb_backup_file:
        new_items = list()

        for k, line in enumerate(ddb_backup_file):
            item_container = json.loads(line)
            item = item_container["Item"]
            if item["pk"]["S"][:4] == "lyr#":
                new_pk = f"{item['pk']['S'].replace('.', ':')}:p3.8"
                item["pk"]["S"] = new_pk
                try:
                    if item["sk"]["S"] != "lyrVrsn0#":
                        item["rgn#PyVrsn"] = {"S": f"{item['rgn']['S']}:p3.8"}
                        item["pckg#PyVrsn"] = {"S": f"{item['pckg']['S']}:p3.8"}
                except KeyError:
                    print("error")
            elif item["pk"]["S"] == "bldVrsn0#":
                new_pk = f"{item['pk']['S']}p3.8"
                item["pk"]["S"] = new_pk
                item["bltVrsn"]["N"] = item["bltVrsn"]["S"][len("bld#v") :]
                item["bltVrsn"].pop("S")
            elif item["pk"]["S"][:5] == "bld#v":
                new_pk = f"{item['pk']['S']}:p3.8"
                item["pk"]["S"] = new_pk
                item["bltVrsn"]["N"] = item["bltVrsn"]["S"][len("bld#v") :]
                item["bltVrsn"].pop("S")
            else:
                print(f"Unknown: {item}")
                write_error_to_file(error_item=item)
                continue  # skip and move to next item.

            item["pyVrsn"] = {"S": "p3.8"}
            new_items.append(item)

    with open(output_file, "w") as output:
        for item in new_items:
            output.write(json.dumps(item))
            output.write("\n")


if __name__ == "__main__":
    download_directory = "downloads"
    output_directory = "output"

    shutil.rmtree(download_directory)
    os.mkdir(download_directory)
    shutil.rmtree(output_directory)
    os.mkdir(output_directory)
    client_token = datetime.datetime.now().isoformat()
    s3_prefix = export_to_s3(client_token=client_token)

    download_objects_from_s3(s3_prefix=s3_prefix)

    downloaded_jsons = os.listdir("downloads")

    for k, json_file in enumerate(downloaded_jsons):
        modify_data(
            input_file=f"./downloads/{json_file}", output_file=f"./output/{k}.json"
        )

    for _x in range(k + 1):
        with open(f"./output/{_x}.json", "r") as input_file:
            items = input_file.readlines()
        load_data(items)
    print(f"Wrote out data from {k+1} files")
