import packaging
import requests
import json

from packaging.version import parse


def get_latest_release(package):
    """
    Args:
      package: Name of package to be queried
    returns:
      version: Version number of latest release that is **not**  a pre-release
    """
    req = requests.get(f"https://pypi.python.org/pypi/{package}/json")
    version = parse('0')
    if req.status_code == requests.codes.ok:
        j = json.loads(req.text)
        releases = j.get('releases', [])
        for release in releases:
            ver = parse(release)
            if not ver.is_prerelease:
                version = max(version, ver)

    return version


def install(package):

    import subprocess
    subprocess.run(["pip", "install", package, "-t", f"/tmp/{package}"], capture_output=True)
    return 


def main(event,context):

    package = event['package']
    latest_release = get_latest_release(package)


    return True


if __name__ == '__main__':
    main({"package": "requests"}, {})

