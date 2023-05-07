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
