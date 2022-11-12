This directory contains the Serverless deployment for a sandbox build from github.

A comment on the pull request in Github from me (Keith), with the the @KlayersBot prefix will invoke the step function in this directory (the `01_on_issue_comment` directory to be exact)

Unlike the other deployments, this one **always** build in the Klayers-devp38 environment, as it's a non-prod environment and relative stable. Unlike Klayers-defaultp38 which sometimes goes through lots of change in a short period of time, and we definitely do not want to build in the production.

To install

    $ npm install
    $ serverless plugin install --name serverless-step-functions
    $ serverless plugin install --name serverless-better-credentials

To use SSO credentials

    $ export AWS_SDK_LOAD_CONFIG=1
    $ aws sso login --profile KlayersDev
