# Keith's Layers (Klayers)

[![Python 3.7](https://img.shields.io/badge/python-3.7-green.svg)](https://www.python.org/downloads/release/python-360/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/keithrozario/Klayers.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/keithrozario/Klayers/context:python)


A collection of AWS Lambda Layers for Python3.7

# Status of layers

[![Updates](https://pyup.io/repos/github/keithrozario/Klayers/shield.svg)](https://pyup.io/repos/github/keithrozario/Klayers/)

Click on badge above to see the specific package version of the latest builds. 

Layers are built with the latest package version (available on PyPI) every Monday at 1:00am (UTC)

# Layer List

All layers are publicly available with the following ARN pattern:

arn:aws:lambda:\<**region**>:113088814899:layer:\<**Layer Name**>:\<**version**>

Full list of publicly available layers by region are [here](arns/).

# Python Packages

All packages below were built with the Python 3.7 runtime. May (or may not) work with Python 3.6. View [here](https://pyup.io/repos/github/keithrozario/Klayers/) for detail list of package versions.

| Package        | Layer Name              |         
| :------------- |:----------------------- |
aiobotocore| Klayers-python37-aiobotocore
aiohttp|Klayers-python37-aiohttp
ansible|Klayers-python37-ansible
arrow|Klayers-python37-arrow
aws-xray-sdk|Klayers-python37-aws-xray-sdk
bcrypt|Klayers-python37-bcrypt
beautifulsoup4|Klayers-python37-beautifulsoup4
boltons|Klayers-python37-boltons
boto3|Klayers-python37-boto3
construct|Klayers-python37-construct
elasticsearch|Klayers-python37-elasticsearch
envelopes|Klayers-python37-envelopes
ffmpeg-python|Klayers-python37-ffmpeg-python
flashtext|Klayers-python37-flashtext
google-auth|Klayers-python37-google-auth
google-auth-oauthlib|Klayers-python37-google-auth-oauthlib
grpcio|Klayers-python37-grpcio
gspread|Klayers-python37-gspread
idna|Klayers-python37-idna
itsdangerous|Klayers-python37-itsdangerous
kafka-python|Klayers-python37-kafka-python
nltk|Klayers-python37-nltk
numpy|Klayers-python37-numpy
opencv-python-headless|Klayers-python37-opencv-python-headless
openpyxl|Klayers-python37-openpyxl
pandas|Klayers-python37-pandas
Pillow|Klayers-python37-Pillow
PyJWT|Klayers-python37-PyJWT
pymongo|Klayers-python37-pymongo
PyMUPDF|Klayers-python37-PyMUPDF
PyMySQL|Klayers-python37-PyMySQL
PyNaCl|Klayers-python37-PyNaCl
pyOpenSSL|Klayers-python37-pyOpenSSL
pyparsing|Klayers-python37-pyparsing
pytesseract|Klayers-python37-pytesseract
python-docx|Klayers-python37-python-docx
python-Levenshtein|Klayers-python37-python-Levenshtein-wheels
pytz|Klayers-python37-pytz
PyYAML|Klayers-python37-PyYAML
requests|Klayers-python37-requests
scipy|Klayers-python37-scipy
simplejson|Klayers-python37-simplejson
spacy|Klayers-python37-spacy
SQLAlchemy|Klayers-python37-SQLAlchemy
tinydb|Klayers-python37-tinydb
tldextract|Klayers-python37-tldextract

# Using the Layers

You can either:
* Set any of the ARNs below (for your region) to be a layer for your function. 
* Use the `Get Layer Version by ARN` in [python](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.get_layer_version_by_arn) or [bash](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-layer-version-by-arn.html) command which will provide an S3 location to download the layer as a zip

Currently only the following regions have the layers deployed click the links for the full list of layer arns:

* [ap-northeast-1](arns/ap-northeast-1.json) 
* [ap-northeast-2](arns/ap-northeast-2.json)
* [ap-south-1](arns/ap-south-1.json)
* [ap-southeast-1](arns/ap-southeast-1.json) 
* [ap-southeast-2](arns/ap-southeast-2.json)
* [ca-central-1](arns/ca-central-1json)
* [eu-central-1](arns/eu-central-1.json)
* [eu-north-1](arns/eu-north-1.json)
* [eu-west-1](arns/eu-west-1.json)
* [eu-west-2](arns/eu-west-2.json)
* [eu-west-3](arns/eu-west-3.json)
* [sa-east-1](arns/sa-east-1.json)
* [us-east-1](arns/us-east-1.json)
* [us-east-2](arns/us-east-2.json)
* [us-west-1](arns/us-west-1.json)
* [us-west-2](arns/us-west-2.json)
* [ap-east-1](arns/ap-east-1.json)
* [me-south-1](arns/me-south-1.json)

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


# Layer specific notes

For `pip` you'll need to set your PYTHONPATH to `/opt/python` to override the existing pip inside the lambda environment.

For `spacy`, this is version 2.2 and above (without the language files). You'll need to bring your own language files/model.

# To DO
* ~~Cleanup script to delete all lamba layers that are not the latest version (and more than x days old)~~ Done using TTL on DynamoDB
* ~~Schedule this to run everyday for production~~ Currently runs once a week on Monday
* Package openssl v1.1.x for better encryption of KEK
* Blog post and architecture review (WIP: [here](https://www.keithrozario.com/2019/08/klayers-part-0-introduction.html))

# Architecture Diagram

Diagram is still pretty draft will add more details later!

![Screenshot](documentation/Klayers-Architecture.png)

# Special Thanks

[Chahna107](https://github.com/chahna107) for adding tesseract config files into the tesseract layer.