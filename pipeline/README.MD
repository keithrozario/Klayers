# Klayers Pipeline Architecture

This directory contains the services and infrastructure that power Klayers. Each service is structured as an independent, modular **Python CDK Mini-App** (`infra.py` + `cdk.json` + `pyproject.toml` managed with `uv`), decoupled strictly via **AWS SSM Parameter Store** (zero CloudFormation cross-stack `Export`/`ImportValue` locks).

All deployments run on **GitHub Actions** promoting sequentially across **GitHub Environments** (`default` -> `dev` -> `prod`).

---

## Component Overview

### 1. `Terraform/`
Maintains foundational stateful cloud resources:
- DynamoDB table (`db-ver2`)
- CloudFront ACM certificate (`us-east-1`)
- S3 buckets (layers storage and config)
- ECR container repositories
- GitHub Actions OIDC roles (`github_role_default`, `github_role_dev`, `github_role_prod`)

### 2. `common_services/` (Stack: `klayers-common-<stage>`)
Central configuration microservice:
- Provides SigV4 IAM-authorized HTTP API (v2) routes:
  - `GET /api/v1/python-versions`
  - `GET /api/v1/config/{python_version}/{config_type}`
  - `GET /api/v1/configS3/{python_version}/{config_type}`
  - `POST /api/v1/load-config`
- Lambda functions running Python 3.13.
- Publishes SSM parameters:
  - `/common-service/<stage>/CommonServiceApi/URL`
  - `/common-service/<stage>/CommonServiceApi/arn`

### 3. `container_images/`
Container build system for Lambda Layer builders:
- Single parameterized `Dockerfile` (`ARG BASE_IMAGE_TAG`) + `build.py`.
- Automated GitHub Actions matrix builds using native runners:
  - `ubuntu-latest` for `x86_64`
  - `ubuntu-24.04-arm` for `arm64` (native ARM64 execution, no QEMU emulation)
- Builds once and promotes exact OCI image digests across environment ECR repositories.
- Updates SSM digest parameters `/kl/<stage>/build/<py>/<arch>/digest`.

### 4. `core_pipeline/` (Stack: `klayers-core-<stage>`, formerly `Serverless/`)
The primary build and publication engine:
- Data-driven Python CDK stack dynamically synthesizing `Build<PyVer>` container Lambdas and Step Function `Choice` branches from `config/config.json`.
- State Machines orchestrating package build, verification, multi-region layer deployment, and DynamoDB updates.
- DynamoDB Stream processor for TTL layer expiration.
- Slack notifications service using `slack_sdk`.

### 5. `api/` (Stack: `klayers-api-<stage>`)
Public read-only API and CloudFront CDN distribution:
- Serves `api.klayers.cloud` (and `api-dev.klayers.cloud`, `api-default.klayers.cloud`).
- Lambda functions on Python 3.13 (`arm64` Graviton) querying DynamoDB and returning JSON, CSV, and HTML views of available layers.

### 6. `github_on_pr_merge/` (Stack: `klayers-gh-push-<stage>`)
Event handler invoked when community PRs add new packages to CSV files:
- Validates changes and triggers the build pipeline Step Function.

---

## Environments & Promotion Pipeline

All deployments operate from a single trunk (`master`) through three isolated AWS accounts:

| GitHub Environment | Legacy Stage Name (`STAGE`) | AWS Account ID | Primary Region | S3 Config Source | API Domain |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`default`** | `Klayers-defaultp38` | `367660174341` | `ap-southeast-1` | `pipeline/config/test_config` | `api-default.klayers.cloud` |
| **`dev`** | `Klayers-devp38` | `908645878701` | `us-west-2` | `pipeline/config/test_config` | `api-dev.klayers.cloud` |
| **`prod`** | `Klayers-prodp38` | `770693421928` | `us-east-2` | `pipeline/config` | `api.klayers.cloud` |

### Promotion Flow
```
Merge to master (or workflow_dispatch)
  ↓
Test & Synth (uv run pytest + cdk synth)
  ↓
Deploy: default (ap-southeast-1)
  ↓
Deploy: dev (us-west-2)
  ↓
GitHub Approval Gate (prod)
  ↓
Deploy: prod (us-east-2)
```

---

## Simplified Workflow: Adding a New Version of Python

With the parameterized container images and dynamic CDK mini-app loops, adding a new Python runtime (e.g. `p3.15` and `p3.15-arm64`) requires zero YAML copy-pasting:

1. **Add ECR Repositories**:
   Add the ECR module in `pipeline/Terraform/container_repositories.tf` and apply via Terraform.

2. **Update Configuration**:
   Add `"p3.15"` and `"p3.15-arm64"` to `python_versions` and configure their package file references in `pipeline/config/config.json` (and `pipeline/config/test_config/config.json`).
   Create initial `pipeline/config/packages_p3.15.csv` and `pipeline/config/packages_p3.15-arm64.csv` with standard CSV headers.

3. **Commit & Push to `master`**:
   - `deploy-containers.yml` automatically detects the new versions, builds the x86 and ARM64 container images in parallel on native runners, and pushes to ECR.
   - `deploy-core-pipeline.yml` reads `config.json` and dynamically instantiates the new `BuildP315` and `BuildP315Arm64` Lambdas and wires their Step Function `Choice` branches.
   - `load_config` in `common_services` populates DynamoDB with the new Python versions and package lists.

4. **Add Desired Packages**:
   Add package rows to `packages_p3.15.csv` and push to start building layers automatically!
