def get_compatible_runtimes(python_version: str) -> list:
    """
    Args:
        python_version: In the form of (p3.8, p3.10-arm64, etc)
    return:
        compatible_runtime: In the form of accepted here: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
    """

    compatible_runtime = python_version.split("-")[0].replace("p", "python")
    return [compatible_runtime]


def get_compatible_architectures(python_version: str) -> list:
    """
    Args:
        python_version: In the form of (p3.8, p3.10-arm64, etc)
    return:
        compatible_architectures: In the form of accepted here: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
    """
    compatible_architecture = "x86_64"  # default value if none provided
    if python_version.endswith("arm64"):
        compatible_architecture = "arm64"

    return [compatible_architecture]
