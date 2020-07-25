import os
import json
import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools.logging import Logger

logger = Logger()


@logger.inject_lambda_context
def main(event, context):
    """
    Args:
        event.pathParameter.region: AWS region
        event.pathParameter.package: Python Package
    returns:
        api_response: Dictionary containing, region, package, arn and requirements.txt data
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ['DB_NAME'])
    region = event.get('pathParameters').get('region')
    package = event.get('pathParameters').get('package')

    pk = f"lyr#{region}.{package}"
    sk = "lyrVrsn0#"

    try:
        response = table.get_item(
            Key={'pk': pk, 'sk': sk},
            AttributesToGet=[
                'rgn','pckg','arn','rqrmntsTxt','pckgVrsn'
            ],
        )
        api_response = {
            "region": response['Item']['rgn'],
            "package": response['Item']['pckg'],
            "arn": response['Item']['arn'],
            "dependencies": response['Item']['rqrmntsTxt'].split('\n'),
            "version": response['Item']['pckgVrsn'],
        }
    except ClientError as e:
        logger.error({
            "message": response['Error']['Message'],
            "pk": pk,
            "sk": sk,
        })
        api_response = {}
    except KeyError as e:  # no item return
        api_response = {}
    
    return {
        "statusCode": 200,
        "body": json.dumps(api_response),
    }
