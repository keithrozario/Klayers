# Intro

This directory contains the various services that make up Klayers.

## Terraform
Contains the terraform scripts that create the buckets, dynamodb tables, ECR registry, etc. This is the main infra for all services and should be deployed first.

## common_services
Contains common services used by most of the other services. Terraform and the common services should be deployed first before any other service further below this list.

## container_images
Contains the container images used for building the layers. These are pushed via scripts to ECR

## Serverless
Contains the Serverless scripts for the main build pipeline

## API
Contains the Serverless scripts for the API (api.klayers.cloud)

## github_on_pr_merge
The main functionality (step functions) for when a PR is merged in github. see also the `.github/workflows` for more info.

## To add a new version of Python

* Update `Terraform/container_repositories.tf` to reflect new containers for building with new version of Python
* Update `container_images/build_images` with new folder for new version of Python
* Update `Serverless/02_pipeline/pipeline_build_containers.yml` to create new build function
* Update `Serverless/state_machines/02_pipeline.yml` to update build step function to use new functions
* Update `config/test_config/config.json` to include new python versions (or remove old ones)
    * Remember to do the same for `config` as well. `test_config` is used by klayers-default and klayers-dev
* Push update to `klayers-default`, `klayers-dev` and `klayers-prod` branch so that Github-Actions can push update to s3
    * For simplicity ensure the config csvs do not have packages, (but have headers)
* Run `common_services/load_config_from_s3` lambda functions to load new config from s3 to DynamoDB
    * sls invoke -f load_config -s <stage>
    * sls invoke -f check_python_versions -s <stage>
        * this function has a heavy cache, you might have to clear it
* Update new packages in `config/packages_<pythonversion>.csv`
    * push to branch to start building
* Run `invoke_pipeline` to invoke new pipelines

