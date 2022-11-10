import os
import boto3


def get_config_items(config_type: str, python_version: str = "p.38") -> list:
    """
    Args:
        python_version: Version of Python
        config_type: Type of config items (e.g pckg)
    returns:
        config_items : List of configuration items
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DB_NAME"])

    response = table.get_item(Key={"pk": f"cnfg#{config_type}", "sk": python_version})
    config_items = response["Item"]["cnfg"]

    return config_items