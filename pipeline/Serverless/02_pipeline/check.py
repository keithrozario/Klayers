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
    req = requests.get(f"https://pypi.python.org/pypi/{package}/json")
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


def main(event, context):
    """
    Args:
      package: Package to check for
    return:
      package: Name of package
      version: Version of package to deploy
      license_info: License as per PyPI
    """

    logger.debug(event)
    package = event.get("detail").get("package")

    logger.debug(f"Checking {package}")

    latest_version, license_info = get_latest_release(package)
    logger.info(f"Latest version of package:{package} on pypi is {latest_version}")

    # Layer license has a hard limit of 512
    if len(license_info) > 512:
        license_info = license_info[:500] + "..."

    return {
        "version": str(latest_version),
        "package": package,
        "license_info": license_info,
    }
