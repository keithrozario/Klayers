# Serverless

This directory contains the Serverless repository of lambda functions.

## Functions

Functions and their corresponding `.yml` files are stored in individual folders.

## Step Functions

Step function configuration uses the `serverless-step-functions` plugin, with corresponding `.yml` files stored in the /state_machines folder.

## Installation

serverless plugin install -n serverless-step-functions
serverless plugin install -n serverless-iam-roles-per-function
serverless plugin install -n serverless-better-credentials

export AWS_SDK_LOAD_CONFIG=1
