To Setup

    $ serverless plugin install --name serverless-iam-roles-per-function
    $ serverless plugin install --name serverless-step-functions
    $ serverless plugin install --name serverless-better-credentials
    $ export AWS_SDK_LOAD_CONFIG=1

To run

    $ sls deploy -s $STAGE