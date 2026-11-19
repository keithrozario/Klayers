import os
from functools import lru_cache
from typing import Any

import boto3


@lru_cache(maxsize=64)
def get_config_items(config_type: str, python_version: str = "p.38") -> Any:
    """Args:
        config_type: What type of config item (e.g. pyVrsns, pckgs, rgns)
        python_version: Version of Python (e.g. all, p3.13)

    Returns:
        config_items : List of configuration items
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DB_NAME"])

    response = table.get_item(Key={"pk": f"cnfg#{config_type}", "sk": python_version})
    config_items = response["Item"]["cnfg"]

    return config_items
