# Common Services CDK Mini-App

This component provides the central configuration services used across Klayers. It manages configuration data stored in DynamoDB and S3 (supported Python versions, packages, and AWS deployment regions).

## Architecture

This service is a self-contained AWS CDK (Python) mini-app deployed as stack `klayers-common-<stage>`:

- **Runtime**: Python 3.13 for all Lambda functions.
- **Dependency Bundling**: Zero external layer ARNs. Pure-Python dependencies (`aws-lambda-powertools`) are packaged into a local Lambda Layer (`.layer_build/python`) during synthesis via `uv pip install`.
- **API Gateway**: HTTP API (v2) with `AWS_IAM` (SigV4) authorization enabled by default on all routes.
- **State & Storage**:
  - Configuration DynamoDB table (`/kl/<stage>/db-ver2/*`)
  - Config S3 bucket (`/kl/<stage>/config_bucket/*`)

## Endpoints

All endpoints require AWS SigV4 signed requests:

- `GET /api/v1/python-versions` - Returns the list of currently supported Python runtimes.
- `GET /api/v1/config/{python_version}/{config_type}` - Retrieves configuration items (`pckgs` or `rgns`) from DynamoDB.
- `GET /api/v1/configS3/{python_version}/{config_type}` - Retrieves configuration directly from S3 CSV files.
- `POST /api/v1/load-config` - Loads configuration files from S3 and populates DynamoDB records (`cnfg#pyVrsns`, `cnfg#pckgs`, `cnfg#rgns`).

## SSM Parameters Published

Other services resolve this API dynamically via SSM:

- `/common-service/<stage>/CommonServiceApi/URL` - HTTP API endpoint URL.
- `/common-service/<stage>/CommonServiceApi/arn` - HTTP API execution ARN (`arn:aws:execute-api:<region>:<account>:<api_id>/*`).

## Local Development & Testing

Manage dependencies and run tests using `uv`:

```bash
# Install dependencies
uv sync

# Format and lint
uv run ruff format .
uv run ruff check --fix .

# Run unit tests (Moto mock AWS + CDK template assertions)
uv run pytest

# Synthesize CloudFormation template for a specific stage
npx --yes aws-cdk@2 synth -c stage=Klayers-prodp38
```

## Deployment & Promotion

Deployments are automated through GitHub Actions using GitHub Environments:

- Workflow: `.github/workflows/deploy-common-services.yml`
- Environment promotion: `default` -> `dev` -> `prod` (with Keith's approval gate on `prod`).
- Manual deployments: Trigger via `workflow_dispatch` selecting the target environment (`default`, `dev`, `prod`, or `promote_all`).
