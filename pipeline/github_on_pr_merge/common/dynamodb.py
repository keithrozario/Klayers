import json
import decimal
from datetime import datetime


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


# Rename keys from old to new
def map_keys(items):
    """
    Args:
        itams: List of dict items to be mapped
    return:
        items: List of dict items whose keys have been renamed according to map_table below
    """

    map_table = {
        "pckg": "package",
        "lyrVrsn": "layerVersion",
        "pckgVrsn": "packageVersion",
        "rgn": "region",
        "dplySts": "deployStatus",
        "rqrmntsTxt": "dependencies",
        "arn": "arn",
        "exDt": "expiryDate",
        "rqrmntsHsh": "requirementsHash",
    }

    new_items = []
    for item in items:
        new_item = {}
        for k in item.keys():
            if k == "rqrmntsTxt":
                new_item[map_table[k]] = item[k].split("\n")
            if k == "exDt":
                new_item[map_table[k]] = datetime.fromtimestamp(item[k]).isoformat()
            else:
                new_item[map_table[k]] = item[k]
        new_items.append(new_item)

    return new_items
