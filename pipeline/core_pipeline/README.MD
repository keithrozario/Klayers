# Klayers Core Pipeline (CDK Mini-App)

This directory contains the AWS CDK (Python 3.13) mini-app replacing the legacy Serverless Framework service `kl`.

## Architecture & Components

- **10 Control-Plane Zip Lambdas (`python3.13`)**:
  - `invoke_pipeline`: Scheduled cron invocation triggering the pipeline for all packages.
  - `check`: Checks for package versions on PyPI.
  - `deploy`: Publishes layers to target AWS regions and updates DynamoDB.
  - `combine_packages`: Combines multiple packages into a single zip layer.
  - `stream_handler`: DynamoDB Stream consumer routing TTL/expiry events to EventBridge.
  - `layer_delete`: EventBridge handler deleting expired layers across regions.
  - `slack_pipeline`: Slack notification for Step Function pipeline execution errors.
  - `slack_publish`: Slack notification for publish state machine statuses.
  - `post_message_to_slack`: Generic Slack notifications via EventBridge.
  - `slack_invokepipeline`: Slack notification for invoke pipeline errors.
- **6 Dynamic Container Build Lambdas**:
  - Dynamically defined by reading `pipeline/config/config.json` (`python_versions`).
  - Resolves ECR images and digests via SSM parameters (`/kl/{stage}/build/{py_param}/{arch}/digest`).
- **Step Function State Machine (`kl-{stage}-pipeline`)**:
  - `RandomDelay` -> `Check` -> `ChoicePythonVersion` (dynamic branches per `config.json`) -> `Build*` -> `Deploy` -> `Done`.
  - Includes retry policies for `Lambda.ResourceConflictException` and `Lambda.CodeArtifactUserPendingException`.
- **Self-Contained Layer**:
  - Bundles dependencies from `requirements.txt` via `uv` into a local layer (`.layer_build/python`). Zero external layer ARNs.

## Local Development & Testing

```bash
# Run linter and formatter
uv run ruff check .
uv run ruff format .

# Run unit tests
uv run pytest -v

# Synthesize CloudFormation template
KLAYERS_OFFLINE_SYNTH=1 npx --yes aws-cdk@2 synth -c stage=Klayers-prodp38
```
