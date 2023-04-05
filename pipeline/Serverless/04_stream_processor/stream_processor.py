import json
import os
from datetime import datetime

import boto3
from aws_lambda_powertools.logging import Logger

logger = Logger()


@logger.inject_lambda_context
def main(event, context):
    records = event.get("Records", [])
    entries = []
    stream_label = os.environ["STREAM_LABEL"]
    logger.info(
        {
            "record_count": len(records),
            "stream": stream_label,
        }
    )

    for record in records:
        keys = record.get("dynamodb").get("Keys")

        pk = keys["pk"]["S"]
        sk = keys["sk"]["S"]

        # pk and sk are prefixed with <type>#, every char before the '#' describes the attribute type
        pk_type = pk[: pk.find("#")]
        sk_type = sk[: sk.find("#")]

        event_name = record["eventName"]

        logger.info(
            {
                "pk": pk,
                "pk_type": pk_type,
                "sk": sk,
                "sk_type": sk_type,
                "event_name": event_name,
            }
        )

        entry = {
            "Source": f"{stream_label}",
            "Resources": [],
            "DetailType": event_name,
            "Detail": json.dumps(
                {"pk_type": pk_type, "sk_type": sk_type, "record": record}
            ),
            "EventBusName": "default",
        }
        entries.append(entry)

    client = boto3.client("events")
    response = client.put_events(Entries=entries)
    logger.debug(entries)
    logger.info(
        {
            "num_entries": len(records),
            "failed_entries": response["FailedEntryCount"],
        }
    )

    return
