# Keith's Layers (Klayers)

A collection of AWS Lambda Layers for Python3.7

# Status of layers

[![Updates](https://pyup.io/repos/github/keithrozario/Klayers/shield.svg)](https://pyup.io/repos/github/keithrozario/Klayers/)

If the layers are ever outdated, click the badge above for more info.

Full list of publicly available layers by region are in the `arns` folder of this repo.

# Layer List

## Python Packages (in alphabetical order)

| Package        | ARN                                                                             |         
| :------------- |:------------------------------------------------------------------------------- |
| aiohttp        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-aiohttp:5        |
| bcrypt         | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-bcrypt:3         |
| beautifulsoup4 | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-beautifulsoup4:4 |
| construct      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-construct:1      |
| elasticsearch  | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-elasticsearch:2  |
| ffmpeg-python  | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-ffmpeg-python:3  |
| Pillow         | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-Pillow:5         |
| pymongo        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pymongo:1        |
| PyMuPDF        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-PyMuPDF:1        |
| pyOpenSSL      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pyOpenSSL:4      |
| pytesseract    | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pytesseract:1    |
| pytz           | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pytz:1           |
| requests       | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-requests:4       |
| spacy          | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-spacy:1          |
| tldextract     | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-tldextract:4     |


## Boto3

| Package        | ARN                                                                             | Version |        
| :------------- |:------------------------------------------------------------------------------- | ------- |
| boto3          | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-boto3:1          | 1.9.135 |
| boto3          | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-boto3:2          | 1.9.169 |


## Binaries

| Package        | ARN                                                                             | Version    |         
| :------------- |:------------------------------------------------------------------------------- | ---------- | 
| tesseract      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers--tesseract:1              | 4.1.0-rc1<sup>1</sup>|
| pip            | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pip:2            | 19.2.1     | 

<sup>1</sup> Includes leptonica-1.76.0, libjpeg 6b (libjpeg-turbo 1.2.90) : libpng 1.2.49 : libtiff 4.0.3 : zlib 1.2.8 : libwebp 0.3.0

# Using the Layers

You can either:
* Set any of the ARNs above (for your region) to be a layer for your function. 
* Use the 

Currently only the following regions have the layers deployed:

* ap-northeast-1 
* ap-northeast-2
* ap-south-1
* ap-southeast-1 
* ap-southeast-2
* ca-central-1
* eu-central-1
* eu-north-1
* eu-west-1
* eu-west-2
* eu-west-3
* sa-east-1
* us-east-1
* us-east-2
* us-west-1
* us-west-2

# Layer history

Whenever there is an new version of the underlying package, a new layer **may** be created with an incremented version number.

# Building your own layer

You can use the scripts available in the `infra/` (terraform) and `serverless/` (serverless) directories

For a more old-skool way of deployment using Docker containers, you can refer to the `scripts/build_with_docker` package

# Asking for more layers

Make a pull requests!

# Notes

I intend to delete older layers after a while. Functions relying on deleted layers will still work after the layers are deleted. But you won't be able to create new functions referencing older layers.

# Layer specific notes

For `tldextract`, set the following environment variable to avoid trying to query the Mozilla tld file from the internet.

    $ TLDEXTRACT_CACHE=/opt/python/tldextract/.tld_set_snapshot

For `pytesseract`, the tesseract binary is not included in the build, but the layer includes Pillow. To use tesseract you'd need the tesseract binary layer as well.

For `spacy`, I had to manually tweak a few things to make the package fit into a layer, it only works for English, consider this beta. To use the included model:
    
    $ spacy.load('/opt/en_core_web_sm-2.1.0')

For `boto3`, the current version (as of Apr-2019) of boto3 available in the lambda environment is 1.9.42 for python 3.7 which is ~5 months out of date, and ~100 versions ago. Placing the latest version of boto3 in case anyone needs it.

# Special Thanks

[Chahna107](https://github.com/chahna107) for adding tesseract config files into the tesseract layer.