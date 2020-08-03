import boto3
import os
import uuid

from lambda_cache import ssm

from aws_lambda_powertools.logging import Logger

logger = Logger()


@logger.inject_lambda_context
@ssm.cache(parameter=os.environ["DISTRIBUTION_NAME"])
def main(event, context):
    distribution_id = getattr(context, "id")
    CallerReference = str(uuid.uuid4())

    client = boto3.client("cloudfront")
    response = client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            "Paths": {"Quantity": 1, "Items": ["/api/v1/*",]},
            "CallerReference": CallerReference,
        },
    )

    logger.info(
        {
            "CallerReference": CallerReference,
            "message": f"Invalidated Cache for {distribution_id}",
            "invalidation_location": response["Location"],
        }
    )

    return response["Location"]
