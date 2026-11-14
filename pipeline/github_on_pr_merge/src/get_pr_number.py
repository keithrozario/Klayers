import requests
from aws_lambda_powertools.logging import Logger

logger = Logger()
repo = "keithrozario/klayers"


@logger.inject_lambda_context
def main(event, context) -> dict:
    """Args:
        event: Github Event as passed into the State Machine
    Return:
        pr_number: PR Number associated with the commits in the github event
    """
    commit_sha = event.get("after", False)

    if commit_sha:
        response = requests.get(f"https://api.github.com/repos/{repo}/commits/{commit_sha}/pulls")
        logger.info(response.content)
        try:
            data = response.json()
            pr_number = data[0]["number"] if isinstance(data, list) and len(data) > 0 else False
        except Exception as e:
            logger.warning(f"Failed to parse PR number: {e}")
            pr_number = False
    else:
        pr_number = False

    return {"pr_number": pr_number}
