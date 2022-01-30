# Keith's Layers (Klayers)

🐍 A collection of Python Packages as AWS Lambda(λ) Layers 🐍

[![Python 3.8](https://img.shields.io/badge/python-3.8-green.svg)](https://www.python.org/downloads/release/python-380/) [![Python 3.8](https://img.shields.io/badge/python-3.9-green.svg)](https://www.python.org/downloads/release/python-390/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/keithrozario/Klayers.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/keithrozario/Klayers/context:python) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) 

## Layer List

List of all layer version arns are available by region [here](deployments/python3.8/arns)

There might be multiple versions for a single package, as we publish a new layer version if the package dependencies (`requirements.txt`) has been updated. Refer to [Layer expiry](#Layer-expiry) for more data.

*Note: We have deprecated layers for python3.6 and python 3.7, please use these newer versions that are built for python 3.8 and python 3.9 going forward.*

## Python Packages

| Region (Code) | Region (Name)| ARNs|
| :------------- |:--------|:--------|
| af-south-1 |Africa (Cape Town)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/af-south-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/af-south-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/af-south-1/html))|
| ap-east-1 | Asia Pacific (Hong Kong)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-east-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-east-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-east-1/html))|
| ap-northeast-1 |Asia Pacific (Tokyo)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-northeast-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-northeast-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-northeast-1/html))|
| ap-northeast-2 |Asia Pacific (Seoul)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-northeast-2/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-northeast-2/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-northeast-2/html))|
| ap-south-1 |Asia Pacific (Mumbai)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-south-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-south-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-south-1/html))|
| ap-southeast-1 |Asia Pacific (Singapore)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-southeast-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-southeast-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-southeast-1/html))|
| ap-southeast-2 |Asia Pacific (Sydney)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-southeast-2/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-southeast-2/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-southeast-2/html))|
| ap-southeast-3 |Asia Pacific (Jakarta)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-southeast-3/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-southeast-3/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ap-southeast-3/html))|
| ca-central-1 |Canada (Central)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/ca-central-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ca-central-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/ca-central-1/html))|
| eu-central-1 |EU (Frankfurt)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-central-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-central-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-central-1/html))|
| eu-north-1 |EU (Stockholm)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-north-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-north-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-north-1/html))|
| eu-south-1 |EU (Milan)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-south-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-south-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-south-1/html))|
| eu-west-1 |EU (Ireland)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-west-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-west-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-west-1/html))|
| eu-west-2 |EU (London)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-west-2/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-west-2/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-west-2/html))|
| eu-west-3 |EU (Paris)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-west-3/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-west-3/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/eu-west-3/html))|
| me-south-1 |Middle East (Bahrain)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/me-south-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/me-south-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/me-south-1/html))|
| sa-east-1 |South America (São Paulo)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/sa-east-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/sa-east-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/sa-east-1/html))|
| us-east-1 |US East (N. Virginia)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-east-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-east-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-east-1/html))|
| us-east-2 |US East (Ohio)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-east-2/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-east-2/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-east-2/html))|
| us-west-1 |US West (N. California)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-west-1/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-west-1/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-west-1/html))|
| us-west-2 |US West (Oregon)| [json](https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-west-2/json) \| [csv]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-west-2/csv)) \| [html]((https://api.klayers.cloud//api/v2/p3.9/layers/latest/us-west-2/html))|


## Using the Layers

You can use the layers anyway you see fit, here are 4 proposed options:

### Option 1: Set ARN as layer

Click links below for your preferred version of python, and then select your region of choice, you will see a full list of layer version ARNs to use.

* [Arns](deployments/python3.8)

Once selected, you can add the arn directly from the console, by selecting Layers->Add a Layer->Specify an Arn:

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

## Status of layers

Layers are built with the latest package version at 2am UTC on the first Sunday of the Month.

## Layer expiry

Some layer versions will have a `expiry_date` field. This is the date for when the layers will be deleted.

In general, layers are scheduled for deletion 365 days after a new layer version has been published for that package. If you use that latest version of a layer, you're guaranteed at least 365 days before the layer is deleted.

All functions deployed with a layer will still work indefinitely, but you won't be able to deploy new functions referencing a deleted layer version.

## Binaries

Special hand-crafted binaries for layers. These layers are not automatically built, and hence slower update cycles, and will only work with python3.7 functions as the underlying OS is Amazon Linux 1.

| Package        | ARN                                                                             | Version    |
| :------------- |:------------------------------------------------------------------------------- | ---------- |
| en_core_web_sm | arn:aws:lambda:\<*region*>:770693421928:layer:Klayers-python38-spacy_model_en_small:1 | 2.2.5 <sup>2</sup>|
| es_core_news_sm | arn:aws:lambda:\<*region*>:770693421928:layer:Klayers-python38-spacy_model_es_small:1 | 2.3.1 <sup>2</sup>|

<sup>1</sup> Python3.8 layers already have new version of pip, use only if on Python3.7

<sup>2</sup> Spacy [en_core_web_sm](https://spacy.io/models/en) model, for use with the spacy layer refer [here](https://github.com/keithrozario/Klayers/issues/97) for more info.


## Architecture Diagram

![Screenshot](documentation/Klayers-Architecture.png)

## API

We've recently added an API under beta. All API calls are http-based, and work only with https (TLS1.2 and above). The API is heavily cached, so there could be minor delays in updates.

### Get latest ARN for specific package in region

Returns data on the latest layer for a specific *{package}* in a specific *{region}* for your *{python_version}*

*https://api.klayers.cloud/api/v2/{python_version}/layers/latest/{region}/*

example:

  * https://api.klayers.cloud/api/v2/p3.9/layers/latest/us-east-1/
  * https://api.klayers.cloud/api/v2/p3.8/layers/latest/ap-southeast-1/


### Get all ARNs for specific package in region

Returns data on the all layers (latest and deprecated) for a specific *{package}* in a specific *{region}* for your *{python_version}*

*https://api.klayers.cloud/api/v2/{python_version}/layers/{region}/{package}*


example:

  * https://api.klayers.cloud/api/v2/p3.8/layers/us-east-1/requests
  * https://api.klayers.cloud/api/v2/p3.9/layers/ap-southeast-1/boto3


## Special Thanks

* [Chahna107](https://github.com/chahna107) 
* [~ Dependencies scanned by PyUp.io ~](https://pyup.io/)

## Asking for additional layers

If you would like a new package to be made a layer, raise a `pull request` modifying the `pipeline/config/packages_p39.csv` file.
