import json

import requests
from packaging.version import parse

from aws_lambda_powertools.logging import Logger

logger = Logger()


def get_latest_release(package):
    """
    Args:
      package: Name of package to be queried
    returns:
      version: Version number of latest release that is **not** a pre-release as packaging.version
    """
    clean_package_name = package.split("[")[0]
    req = requests.get(f"https://pypi.python.org/pypi/{clean_package_name}/json")
    version = parse("0")
    license_info = None

    if req.status_code == requests.codes.ok:
        j = json.loads(req.text)
        releases = j.get("releases", [])
        for release in releases:
            ver = parse(release)
            if not ver.is_prerelease:
                version = max(version, ver)

        license_info = j.get("info", {}).get("license", None)
        if license_info is None:
            license_info = "No-License-In-PyPI"

    else:
        logger.info("Unable to determine latest version, exiting")
        exit(1)

    return version, license_info


@logger.inject_lambda_context
def main(event, context):
    """
    Args:
      package: Package to check for
      python_version: Version of python (e.g. p3.8, p3.9, p3.10)
    return:
      package: Name of package
      version: Version of package to deploy
      license_info: License as per PyPI
    """

    logger.debug(event)
    package = event.get("detail").get("package")
    python_version = event.get("detail").get("python_version", "p3.8")  # default to 3.8
    force_build = event.get("detail").get("force_build", False)
    force_deploy = event.get("detail").get("force_deploy", False)

    logger.debug(f"Checking {package}")

    latest_version, license_info = get_latest_release(package)
    logger.info(f"Latest version of package:{package} on pypi is {latest_version}")

    # Layer license has a hard limit of 512 characters
    if len(license_info) > 512:
        license_info = license_info[:500] + "..."

    return {
        "version": str(latest_version),
        "package": package,
        "license_info": license_info,
        "python_version": python_version,
        "force_build": force_build,
        "force_deploy": force_deploy,
        "type": 0,  # You must specify a $.type field for a step function choice field, see below
    }


# https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-choice-state.html
# "You must specify the $.type field. If the state input doesn't contain the $.type field, the execution fails and an error is displayed in the execution history."
