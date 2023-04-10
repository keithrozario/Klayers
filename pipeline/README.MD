# Intro

This directoruy contains the various services that make up Klayers.

## Terraform
Contains the terraform scripts that creates the buckets, dynamodb tables, ECR registry, etc. This is the main infra for all services and should be deployed first.

## container_images
Contains the container images used for building the layers. These are pushed via scripts to ECR

## Serverless
Contains the Serverless scripts for the main build pipeline

## API
Contains the Serverless scripts for the API (api.klayers.cloud)

## github_on_pr_merge
The main functionality (step functions) for when a PR is merged in github. see also the the `.github/workflows` for more info.