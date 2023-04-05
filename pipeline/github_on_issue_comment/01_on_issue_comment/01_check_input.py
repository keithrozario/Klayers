import json
import boto3
import datetime
from aws_lambda_powertools.logging import Logger

logger = Logger()

@logger.inject_lambda_context
def main(event, context):
    logger.debug(event)

    detail = event.get("detail")
    package = detail.get("package")
    python_version = detail.get("python_version", "p3.8")
    force_build = detail.get("force_build", True)
    force_deploy = detail.get("force_deploy", True)
    github_comment_id = detail.get("github_comment_id", "")
    github_issue_id = detail.get("github_issue_id", "")
   
    return {
        "version": "0",
        "github_comment_id": github_comment_id,
        "github_issue_id": github_issue_id,
        "time": datetime.datetime.utcnow().isoformat(),
        "detail": {
            "package": package,
            "python_version": python_version,
            "force_build": force_build,
            "force_deploy": force_deploy,
        }
    }