# Keith's Layers (Klayers)

[![Python 3.7](https://img.shields.io/badge/python-3.7-green.svg)](https://www.python.org/downloads/release/python-375/)  [![Python 3.8](https://img.shields.io/badge/python-3.8-green.svg)](https://www.python.org/downloads/release/python-380/)

[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/keithrozario/Klayers.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/keithrozario/Klayers/context:python)

A collection of AWS Lambda Layers for Python

## Layer List

List of all layer version arns are available by region here:

* [Arns](deployments/python3.8/arns)

There might be multiple versions for a single package, this is because we publish a new layer version for every new version of the package or if the package dependencies (`requirements.txt`) has been updated. Refer to [Layer expiry](#Layer-expiry) for more data.

*Note: We have deprecated layers for python3.6 and python 3.7, please use these newer versions that are built for python 3.8 instead.*

## Python Packages

For the full list of packages available click [here](pipeline/config/Klayers-prodp38/packages.csv), here are just some examples of the ~70 packages we build every week:

* aws-lambda-powertools
* aws-xray-sdk
* bcrypt
* beautifulsoup4
* boto3
* dynamodb-encryption-sdk
* idna
* lambda-cache
* nltk
* numpy
* opencv-python-headless
* openpyxl
* pandas
* parliament
* Pillow
* pulp
* pycryptodome
* PyJWT
* PyMUPDF
* pyqldb
* pytesseract
* pytz
* PyYAML
* requests
* slackclient
* spacy

## Status of layers

Click [here](https://pyup.io/account/repos/github/keithrozario/Klayers/settings/) to see specific dependencies of all the latest builds. Layers are built with the latest package version at 2am UTC every Sunday.

## Using the Layers

You can either set one of the ARNs below as a layer in your function. Or download the layer and deploy a copy into your account.

### Option 1: Set ARN as layer

Click links below for your preferred version of python, and then select your region of choice, you will see a full list of layer version ARNs to use.

* [Arns](deployments/python3.8/arns)

### Option 2: Download copy of layer

Use the `Get Layer Version by ARN` in [python](https://boto3.amazonaws.com/v1/documentatio/api/latest/reference/services/lambda.html#Lambda.Client.get_layer_version_by_arn) or [aws-cli](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-layer-version-by-arn.html) command which will provide an S3 location to download the layer as a zip.

*Note: You can only get layers from the specific region your client is configured for, otherwise you'll get a `AccessDeniedException` error.*

## Layer expiry

Some layer versions will have a `expiry_date` field. This is the date for when the layers will be deleted.

In general, layers are scheduled for deletion 60 days after a new layer version has been published for that package. If you use that latest version of a layer, you're guaranteed at least 30 days before the layer is deleted.

All functions deployed with a layer will still work indefinitely, but you won't be able to deploy new functions referencing a deleted layer version.

## Binaries

Special hand-crafted binaries for layers. These layers are not automatically built, and hence slower update cycles, and will only work with python3.7 functions as the underlying OS is Amazon Linux 1.

| Package        | ARN                                                                             | Version    |
| :------------- |:------------------------------------------------------------------------------- | ---------- |
| pip            | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pip:2            | 19.2.1 <sup>1</sup>|     |
| en_core_web_sm | arn:aws:lambda:\<*region*>:770693421928:layer:Klayers-python38-spacy_model_en_small:1 | 2.2.5 <sup>2</sup>|

<sup>1</sup> Python3.8 layers already have new version of pip, use only if on Python3.7

<sup>2</sup> Spacy [en_core_web_sm](https://spacy.io/models/en) model, for use with the spacy layer refer [here](https://github.com/keithrozario/Klayers/issues/97) for more info.

## Architecture Diagram

![Screenshot](documentation/Klayers-Architecture.png)

## Special Thanks

* [Chahna107](https://github.com/chahna107) for adding tesseract config files into the tesseract layer.
* [~ Dependencies scanned by PyUp.io ~](https://pyup.io/)