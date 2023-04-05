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
        "crtdDt": "createdDateTime",
    }

    new_items = []
    for item in items:
        new_item = {}
        for k in item.keys():
            if k == "rqrmntsTxt":
                new_item[map_table[k]] = item[k].split("\n")
            elif k == "exDt":
                new_item[map_table[k]] = datetime.fromtimestamp(item[k]).isoformat()
            elif k == "crtdDt":
                new_item[map_table[k]] = item[k][:19]
            else:
                new_item[map_table[k]] = item[k]
        new_items.append(new_item)

    return new_items


def query_till_end(table, kwargs):
    """
    Args:
        table: DynamoDB table resource
        kwargs: Key word arguments for Query
    return:
        All items in query
    """

    items = list()
    while True:
        response = table.query(**kwargs)
        items.extend(response["Items"])

        try:
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        except KeyError:
            break

    return items
