# Keith's Layers (Klayers)

[![Python 3.7](https://img.shields.io/badge/python-3.7-green.svg)](https://www.python.org/downloads/release/python-375/)  [![Python 3.8](https://img.shields.io/badge/python-3.8-green.svg)](https://www.python.org/downloads/release/python-380/)

[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/keithrozario/Klayers.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/keithrozario/Klayers/context:python)


A collection of AWS Lambda Layers for Python3.7 & Python3.8

# Status of layers

[![Updates](https://pyup.io/repos/github/keithrozario/Klayers/shield.svg)](https://pyup.io/repos/github/keithrozario/Klayers/)

Click on badge above to see the specific package version of the latest builds. 

Layers are built with the latest package version (available on PyPI) every Monday at 1am (python 3.7) and 2am (python3.8) UTC.

# Layer List

All layers are publicly available with the following ARN pattern:

arn:aws:lambda:\<**region**>:113088814899:layer:\<**Layer Name**>:\<**version**>

Full list of publicly available layers by region are [here](deployments/).

# Python Packages

All packages below were built with the Python 3.7 runtime. May (or may not) work with Python 3.6. View [here](https://pyup.io/repos/github/keithrozario/Klayers/) for detail list of package versions.

| Package        | Python3.7               | Python3.8               |
| :------------- |:----------------------- |:----------------------- |
aiobotocore|✅|✅
aiodns|✅|
aiohttp|✅|✅
ansible|✅|✅
aws-lambda-powertools||✅
arrow|✅|✅
aws-xray-sdk|✅|✅
bcrypt|✅|✅
beautifulsoup4|✅|✅
boltons|✅|✅
boto3|✅|✅
construct|✅|✅
dynamodb-encryption-sdk||✅
elasticsearch|✅|✅
envelopes|✅|✅
ffmpeg-python|✅|✅
flashtext|✅|✅
google-auth|✅|✅
google-auth-oauthlib|✅|✅
graphene|✅|
grequests|✅|
grpcio|✅|✅
gspread|✅|✅
idna|✅|✅
itsdangerous|✅|✅
kafka-python|✅|✅
nltk|✅|✅
numpy|✅|✅
opencv-python-headless|✅|✅
openpyxl|✅|✅
pandas|✅|✅
parliament||✅
Pillow|✅|✅
pulp|✅|✅
pycryptodome||✅
PyJWT|✅|✅
pymongo|✅|✅
PyMUPDF|✅|✅
PyMySQL|✅|✅
PyNaCl|✅|✅
pyOpenSSL|✅|✅
pyparsing|✅|✅
pyqldb|✅|✅
pytesseract|✅|✅
python-docx|✅|✅
python-Levenshtein|✅|✅
pytz|✅|✅
PyYAML|✅|✅
reportlab||✅
requests|✅|✅
scipy|✅|
simplejson|✅|✅
spacy|✅|✅
SQLAlchemy|✅|✅
textdistance|✅|✅
tinydb|✅|✅
tldextract|✅|✅

# Using the Layers

You can either set one of the ARNs below as a layer in your function. Or download the layer and deploy a copy into your account.

## Set ARN as layer

Currently only the following regions have the layers deployed click the links for the full list of layer arns:

| Region         | ARNs                    | ARNs                    |
| :------------- |:----------------------- |:----------------------- |
ap-northeast-1|[python3.7](deployments/python3.7/arns/ap-northeast-1.json)|[python3.8](deployments/python3.8/arns/ap-northeast-1.json)
ap-northeast-2|[python3.7](deployments/python3.7/arns/ap-northeast-2.json)|[python3.8](deployments/python3.8/arns/ap-northeast-2.json)
ap-south-1|[python3.7](deployments/python3.7/arns/ap-south-1.json)|[python3.8](deployments/python3.8/arns/ap-south-1.json)
ap-southeast-1|[python3.7](deployments/python3.7/arns/ap-southeast-1.json)|[python3.8](deployments/python3.8/arns/ap-southeast-1.json)
ap-southeast-1|[python3.7](deployments/python3.7/arns/ap-southeast-2.json)|[python3.8](deployments/python3.8/arns/ap-southeast-2.json)
ca-central-1|[python3.7](deployments/python3.7/arns/ca-central-1.json)|[python3.8](deployments/python3.8/arns/ca-central-1.json)
eu-central-1|[python3.7](deployments/python3.7/arns/eu-central-1.json)|[python3.8](deployments/python3.8/arns/eu-central-1.json)
eu-north-1|[python3.7](deployments/python3.7/arns/eu-north-1.json)|[python3.8](deployments/python3.8/arns/eu-north-1.json)
eu-west-1|[python3.7](deployments/python3.7/arns/eu-west-1.json)|[python3.8](deployments/python3.8/arns/eu-west-1.json)
eu-west-2|[python3.7](deployments/python3.7/arns/eu-west-2.json)|[python3.8](deployments/python3.8/arns/eu-west-2.json)
eu-west-3|[python3.7](deployments/python3.7/arns/eu-west-3.json)|[python3.8](deployments/python3.8/arns/eu-west-3.json)
sa-east-1|[python3.7](deployments/python3.7/arns/sa-east-1.json)|[python3.8](deployments/python3.8/arns/sa-east-1.json)
us-east-1|[python3.7](deployments/python3.7/arns/us-east-1.json)|[python3.8](deployments/python3.8/arns/us-east-1.json)
us-east-2|[python3.7](deployments/python3.7/arns/us-east-2.json)|[python3.8](deployments/python3.8/arns/us-east-2.json)
us-west-1|[python3.7](deployments/python3.7/arns/us-west-1.json)|[python3.8](deployments/python3.8/arns/us-west-1.json)
us-west-2|[python3.7](deployments/python3.7/arns/us-west-2.json)|[python3.8](deployments/python3.8/arns/us-west-2.json)
ap-east-1|[python3.7](deployments/python3.7/arns/ap-east-1.json)|[python3.8](deployments/python3.8/arns/ap-east-1.json)
me-south-1|[python3.7](deployments/python3.7/arns/me-south-1.json)|[python3.8](deployments/python3.8/arns/me-south-1.json)

## Download copy of layer

* Use the `Get Layer Version by ARN` in [python](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.get_layer_version_by_arn) or [bash](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-layer-version-by-arn.html) command which will provide an S3 location to download the layer as a zip. *Note: You can only get layers from the specific region your awscli is configured for, otherwise you'll get a `AccessDeniedException` error. In python, setup the boto3 client for the same region as the arn you're getting.*

## Layer expiry

Some layers will have a `time_to_live` field. This is the UNIX epoch time for when that layer will be deleted, typically this will be 30 days after a new version is deployed. If you use the latest version of a package, it'll be up for at least 30 days before deletion.

## Binaries

Special hand-crafted binaries for layers. These layers are not automatically built, and hence slower update cycles.

| Package        | ARN                                                                             | Version    |         
| :------------- |:------------------------------------------------------------------------------- | ---------- | 
| tesseract      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-tesseract:1            | 4.1.0-rc1<sup>1</sup>|
| pip            | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pip:2            | 19.2.1     |
| netcat         | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-netcat:2         | 0.7.1<sup>2</sup>|

<sup>1</sup> Includes leptonica-1.76.0, libjpeg 6b (libjpeg-turbo 1.2.90) : libpng 1.2.49 : libtiff 4.0.3 : zlib 1.2.8 : libwebp 0.3.0

<sup>2</sup> netcat-traditional with the -e option -- compiled for 64-bit to run on AWS Lambda

# Architecture Diagram

Diagram is still pretty draft will add more details later!

![Screenshot](documentation/Klayers-Architecture.png)

# Special Thanks

[Chahna107](https://github.com/chahna107) for adding tesseract config files into the tesseract layer.