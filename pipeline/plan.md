# Plan to Upgrade Python Versions to 3.13 and 3.14

This plan outlines the steps to add support for Python 3.13 and 3.14 while removing support for Python 3.10 and 3.11.

## 1. Update Terraform Infrastructure
*   **File:** `pipeline/Terraform/container_repositories.tf`
*   **Remove:** Resources for `p310` (x86/arm64) and `p311` (x86/arm64).
*   **Add:** Resources for `p313` and `p314` (both x86 and arm64) using the module pattern established for `p312`.
    *   Example:
        ```hcl
        module "python313_x86_build" {
          source             = "./container_repository"
          app_name           = var.app_name
          workspace_full_name = local.workspace_full_name
          python_version = "p313"
          architecture = "x86"
        }
        ```
*   **Execution Note:** 
    *   Applied changes successfully for `defaultp38` workspace.
    *   Encountered and fixed region mismatch for `website_bucket` (managed in `us-east-1` via `cloudfront` provider alias).
    *   Updated `variables.tf` to fix type mismatch for `website_domain_name`.
    *   Commented out explicit `profile` in `main.tf` to rely on environment variables.
    *   Verified that Python 3.13 resources already existed; Python 3.11 resources were destroyed and 3.14 created.

## 2. Update Container Build Images
*   **Directory:** `pipeline/container_images/build_images/`
*   **Remove:** Directories `p310_x86`, `p310_arm64`, `p311_x86`, `p311_arm64`.
*   **Add:** Directories `p313_x86`, `p313_arm64`, `p314_x86`, `p314_arm64`.
*   **Action:** Create a `Dockerfile` in each new directory.
    *   Content should be based on `p312_x86/Dockerfile`.
    *   Update base image tags: `FROM public.ecr.aws/lambda/python:3.13` and `FROM public.ecr.aws/lambda/python:3.14`.
    *   Ensure `dnf` commands are retained (valid for Amazon Linux 2023 used in newer runtimes).
    *   Note: `build.py` is copied into these directories by the GitHub workflow, so no need to manually copy it.
*   **Execution Note:**
    *   Created new Dockerfiles for 3.13/3.14.
    *   Removed old build directories.
    *   Updated `.github/workflows/container_builds.yml` to reflect new versions.
    *   Pushed to `container_builds-default` and verified successful GitHub Actions run.
    *   Verified images exist in ECR.

## 3. Update Serverless Build Configuration
*   **File:** `pipeline/Serverless/02_pipeline/pipeline_build_containers.yml`
*   **Remove:** Functions `build310`, `build311`, `build310Arm64`, `build311Arm64`.
*   **Add:** Functions `build313`, `build314`, `build313Arm64`, `build314Arm64`.
*   **Execution Note:**
    *   Files updated.
    *   Switched to `klayers-default` branch for deployment.

## 4. Update Serverless State Machine
*   **File:** `pipeline/Serverless/state_machines/02_pipeline.yml`
*   **Update:** `ChoicePythonVersion` state.
    *   Remove choices for `p3.10`, `p3.11`.
    *   Add choices for `p3.13`, `p3.14`.
*   **Remove:** States `Build310`, `Build311`, `Build310arm64`, `Build311arm64`.
*   **Add:** States `Build313`, `Build314`, `Build313arm64`, `Build314arm64`.
    *   Link new choice branches to these new states.
    *   Set `Next` to `Deploy` (same as existing states).
*   **Execution Note:**
    *   Updated state machine definition.

## 5. Update Configuration Files
*   **Files:** `pipeline/config/config.json` and `pipeline/config/test_config/config.json`
*   **Update:** `python_versions` list.
    *   Remove `p3.10`, `p3.10-arm64`, `p3.11`, `p3.11-arm64`.
    *   Add `p3.13`, `p3.13-arm64`, `p3.14`, `p3.14-arm64`.
*   **Update:** Config keys.
    *   Remove `p3.10`, `p3.11` keys.
    *   Add `p3.13`, `p3.14` etc keys.
*   **Files:** `pipeline/config/packages_*.csv` and `pipeline/config/test_config/packages_*.csv`
    *   Remove old CSVs: `packages_p310*.csv`, `packages_p311*.csv`.
    *   Create new CSVs: `packages_p313.csv`, `packages_p313-arm64.csv`, `packages_p314.csv`, `packages_p314-arm64.csv`.
    *   Content: Header only (`Package_Name,License,Authors/Maintainers`) to start fresh.
*   **Execution Note:**
    *   Updated config JSONs.
    *   Created new CSVs, removed old CSVs.

## 6. Update GitHub Workflows
*   **File:** `.github/workflows/container_builds.yml`
*   **Update:** Matrix strategy.
    *   Remove entries for `p310` and `p311`.
    *   Add entries for `p313` and `p314` (both x86 and arm64).
*   **Deployment Note:** To trigger new container builds, changes must be pushed to the following branches:
    *   `container_builds-default` (maps to `Klayers-defaultp38`)
    *   `container_builds-dev` (maps to `Klayers-devp38`)
    *   `container_builds-prod` (maps to `Klayers-prodp38`)

## 7. Configuration Update & Pipeline Execution
*   **File:** `.github/workflows/on_push.yml`
*   **Note:** This workflow uploads the `config/` directory to S3 and triggers the Step Function.
*   **Deployment Note:** To update the configuration in S3, push changes to:
    *   `klayers-default` (maps to `Klayers-defaultp38`)
    *   `klayers-dev` (maps to `Klayers-devp38`)
    *   `master` (maps to `Klayers-prodp38`)
*   **Execution Note:**
    *   Pushed config changes to `klayers-default`.
    *   Workflow ran successfully, updating S3 config.
    *   Invoked `load_config` lambda -> Success.
    *   Invoked `check_python_versions` -> Confirmed new versions (p3.12, p3.13, p3.14).
    *   **Comprehensive Verification:**
        *   Ran Step Function executions for `idna` and `requests` on:
            *   p3.13 (x86 & arm64)
            *   p3.14 (x86 & arm64)
        *   All 8 executions SUCCEEDED.
    *   **End-to-End Test:**
        *   Populated `packages_p313.csv` and `packages_p314.csv` with `requests` and `idna`.
        *   Pushed config, ran `load_config`, and invoked `invoke_pipeline` lambda.
        *   Verified 4 automatic Step Function executions triggered and SUCCEEDED.

## 8. Next Steps (Execution)
All steps completed and verified.
1.  Terraform updated infrastructure.
2.  Container images built and pushed for Py 3.12/3.13/3.14 (ARM64 base images corrected).
3.  Serverless pipeline updated and deployed.
4.  Configuration updated in S3 and DynamoDB.
5.  Verification tests passed for multiple packages and architectures.
6.  End-to-end `invoke_pipeline` test passed.
