# Keith's Layers (Klayers)

🐍 A collection of Python Packages as AWS Lambda(λ) Layers 🐍

[![Python 3.8](https://img.shields.io/badge/python-3.8-green.svg)](https://www.python.org/downloads/release/python-380/) [![Python 3.8](https://img.shields.io/badge/python-3.9-green.svg)](https://www.python.org/downloads/release/python-390/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/keithrozario/Klayers.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/keithrozario/Klayers/context:python) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

  -   [List of ARNs](#list-of-arns)
  -   [Python Packages](#python-packages)
  -   [Using the Layers](#using-the-layers)
      -   [Option 1: Using the Console](#option-1-using-the-console)
      -   [Option 2: Download copy of layer](#option-2-download-copy-of-layer)
      -   [Option 3: Using Serverless Framework](#option-3-using-serverless-framework)
      -   [Option 4: Using AWS Serverless Application Model (SAM)](#option-4-using-aws-serverless-application-model-sam)
      -   [Option 5: Using Terraform with the Klayers provider](#option-5-using-terraform-with-the-klayers-provider)
  -   [Status of layers](#status-of-layers)
  -   [Layer expiry](#layer-expiry)
  -   [Architecture Diagram](#architecture-diagram)
  -   [API](#api)
      -   [Get latest ARN for all packages in region](#get-latest-arn-for-all-packages-in-region)
      -   [Get all ARNs for specific package in region](#get-all-arns-for-specific-package-in-region)
  -   [Special Thanks](#special-thanks)
  -   [Asking for additional layers](#asking-for-additional-layers)

## List of ARNs

List of the latest layer version arns are available by region:

* [Python 3.8](deployments/python3.8)
* [Python 3.9](deployments/python3.9)

*Note: We have deprecated layers for python3.6 and python 3.7, please use these newer versions that are built for python 3.8 and python 3.9 going forward.*

## Python Packages

For the full list of Python packages, refer to the following, feel free to make a pull requests modifying the files below to requests for newer python versions.

* [Python 3.8](pipeline/config/packages_p38.csv)
* [Python 3.9](pipeline/config/packages_p39.csv)

## Using the Layers

You can use the layers anyway you see fit, here are 4 options based on what method you use to deploy your lambda functions:

### Option 1: Using the Console

Add the arn directly from the console, by selecting Layers->Add a Layer->Specify an Arn:

![Screenshot](documentation/add_arn.png)

### Option 2: Download copy of layer

Use the `Get Layer Version by ARN` in [python](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.get_layer_version_by_arn) or [aws-cli](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-layer-version-by-arn.html) command which will provide an S3 location to download the layer as a zip.

*Note: You can only get layers from the specific region your client is configured for, otherwise you'll get a `AccessDeniedException` error.*

### Option 3: Using Serverless Framework

You can include layers in your deployments, by utilizing the `layers` property at the function level, and setting it to the arn of your choice. You must use layers from the same region as your function:

```yaml
check:
  handler: 02_pipeline/check.main
  description: Checks for package on PyPi via the API
  runtime: python3.9
  timeout: 30
  memorySize: 256
  layers:
  - arn:aws:lambda:${self:provider.region}:113088814899:layer:Klayers-python37-packaging:1
  - arn:aws:lambda:${self:provider.region}:113088814899:layer:Klayers-python38-aws-lambda-powertools:23
```

### Option 4: Using AWS Serverless Application Model (SAM)

Using AWS SAM, you can include layers in your serverless applications.You must use layers from the same region as your function:

```yaml
ServerlessFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: .
    Handler: my_handler
    Runtime: Python3.9
    Layers:
        - arn:aws:lambda:ap-southeast-1:113088814899:layer:Klayers-p39-packaging:1
```

### Option 5: Using Terraform with the Klayer provider

Using Terraform, you can use the [terraform-provider-klayer](https://github.com/ldcorentin/terraform-provider-klayer). The provider uses the API to enable your functions to always reference the latest layer versions.

```terraform
terraform {
  required_providers {
    klayers = {
      version = "~> 1.0.0"
      source  = "ldcorentin/klayer"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

data "klayers_package_latest_version" "pandas" {
  name   = "pandas"
  region = "us-east-1"
}

resource "aws_lambda_function" "test_lambda" {
  filename      = "index.zip"
  function_name = "klayers-test"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "index.handler"
  runtime       = "python3.9"
  layers = [
    data.klayers_package_latest_version.pandas.arn
  ]
}
```

## Status of layers

Layers are built with the latest package version at 2am UTC on the first day of the Month.

If there's a critical issue with a package, which needs a new version of it published, raise an issue for the package, and I'll try my best to perform the deploy.

## Layer expiry

Some layer versions will have a `expiry_date` field. This is the date for when the layers will be deleted.

In general, layers are scheduled for deletion 365 days after a new layer version has been published for that package. If you use that latest version of a layer, you're guaranteed at **least** 365 days before the layer is deleted.

All functions deployed with a layer will still work indefinitely, but you won't be able to deploy new functions referencing a deleted layer version.

## Architecture Diagram

![Screenshot](documentation/Klayers-Architecture.png)

## API

API v2 has been released. Please use v2 going forward, as we'll end v1 by June-2022.

All API calls are http-based, and work only with https (TLS1.2 and above). The API is heavily cached, so there could be minor delays in updates.

### Get latest ARN for all packages in region

Returns data on the latest layer for a all packages in a specific *{region}* for your *{python_version}*. Defaults to json, but both csv and html can be returned as well.

*https://api.klayers.cloud/api/v2/{python_version}/layers/latest/{region}/{format}*

example:

* [https://api.klayers.cloud/api/v2/p3.9/layers/latest/us-east-1/](https://api.klayers.cloud/api/v2/p3.9/layers/latest/us-east-1/)
* [https://api.klayers.cloud/api/v2/p3.8/layers/latest/ap-southeast-1/](https://api.klayers.cloud/api/v2/p3.9/layers/latest/ap-southeast-1/)
* [https://api.klayers.cloud/api/v2/p3.9/layers/latest/ap-southeast-1/csv](https://api.klayers.cloud/api/v2/p3.9/layers/latest/ap-southeast-1/csv)
* [https://api.klayers.cloud/api/v2/p3.9/layers/latest/ap-southeast-1/html](https://api.klayers.cloud/api/v2/p3.9/layers/latest/ap-southeast-1/html)

### Get all ARNs for specific package in region

Returns data on the all layers (latest and deprecated) for a **specific** *{package}* in a specific *{region}* for your *{python_version}*

*https://api.klayers.cloud/api/v2/{python_version}/layers/{region}/{package}*

example:

* [https://api.klayers.cloud/api/v2/p3.8/layers/us-east-1/requests](https://api.klayers.cloud/api/v2/p3.8/layers/us-east-1/requests)
* [https://api.klayers.cloud/api/v2/p3.9/layers/ap-southeast-1/boto3](https://api.klayers.cloud/api/v2/p3.9/layers/ap-southeast-1/boto3)

## Special Thanks

* [Chahna107](https://github.com/chahna107) 
* [~ Dependencies scanned by PyUp.io ~](https://pyup.io/)
* [@ldcorentin](https://github.com/ldcorentin) for making the awesome klayers-provider

## Asking for additional layers

If you would like a new package to be made a layer, raise a `pull request` modifying the `pipeline/config/packages_p39.csv` or `pipeline/config/packages_p38.csv` file (depending on which version of python you use). By default, please request for the latest version of python unless you absolutely need an older version.
