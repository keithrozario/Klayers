import os
import io
import json
import csv
from tabulate import tabulate
import boto3
from boto3.dynamodb.conditions import Key
from aws_lambda_powertools.logging import Logger
from common.dynamodb import DecimalEncoder, map_keys, query_till_end

logger = Logger()


def query_table(region: str, table: str, python_version: str) -> list:
    """
    Args:
      table: DynamoDB table object to query
      region: region to query on
      python_version: version of python (e.g. p3.9, p3.8)
    returns:
      items: items returned from the query
    """

    kwargs = {
        "IndexName": "deployed_in_region_by_python_version",
        "KeyConditionExpression": Key("rgn#PyVrsn").eq(f"{region}:{python_version}")
        & Key("dplySts").eq("latest"),
        "ProjectionExpression": "pckg, arn, pckgVrsn",
    }
    items = query_till_end(table=table, kwargs=kwargs)

    return map_keys(items)


def return_format(data: list, format: str, region: str, python_version: str):
    """
    Args:
      data: Data to be formatted (list of dicts)
      format: Format of data (e.g. csv, html, json)
    returns:
      body: body of data (str)
      headers: Additional HTML headers if required (dict)
    """

    map_header_row = {
        "package": "Package",
        "packageVersion": "Package Version",
        "arn": "arn",
    }
    logger.info(f"Format: {format}")

    if format == "html":
        body = tabulate(data, headers=map_header_row, tablefmt="html")
        headers = {"Content-Type": "text/html"}
    elif format == "csv":
        with io.StringIO() as csvfile:
            fieldnames = ["package", "packageVersion", "arn"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(map_header_row)
            for row in data:
                writer.writerow(row)
            body = csvfile.getvalue()
        headers = {
            "Content-Type": "text/html",
            "Content-Disposition": f'attachment; filename="klayers-{region}-{python_version}.csv"',
        }
    else:  # defaults to json
        body = json.dumps(data, cls=DecimalEncoder)
        headers = {"Content-Type": "application/json"}

    return body, headers


@logger.inject_lambda_context
def main(event, context):
    """
    Gets layer arns for each region and publish to S3
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DB_NAME"])
    region = event.get("pathParameters").get("region")
    python_version = event.get("pathParameters").get("python_version", "p3.8")
    format = event.get("pathParameters").get("format", "json")
    api_response = query_table(
        table=table, region=region, python_version=python_version
    )

    body, headers = return_format(
        data=api_response, format=format, region=region, python_version=python_version
    )

    return {
        "statusCode": 200,
        "headers": headers,
        "body": body,
    }
