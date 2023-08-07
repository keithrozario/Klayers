# Intro

This is a common service used to load configuration into DynamoDB. This configuration is then read by other services.

Some services may even trigger a new loading of configuration:
    * When the monthly build processes, we trigger a new load to ensure we're building all the latest packages
    * After a PR is merge and after `on_pr_merge` service has run, we'll load the latest packages to ensure we don't duplicate builds

Load config by default runs on all python versions as specified in `pipelines/config/config.json`. This file is uploaded to the config S3 bucket on every push to the respective branches:

    * klayers-default -> Default
    * klayers-dev -> Dev
    * master -> Production

Refer to `.github/workflows/on_push.yml` for more info on the files get updated.

# API

Common services are exposed via an API Gateway with Sigv4 authentication turned on. Every function that calls this API must call it via Sigv4. The API URL is available in ssm at:

    * /kl/common/stage/api/url

# Installation

To Setup

    $ serverless plugin install --name serverless-iam-roles-per-function
    $ serverless plugin install --name serverless-better-credentials
    $ export AWS_SDK_LOAD_CONFIG=1

To run

    $ sls deploy -s $STAGE
