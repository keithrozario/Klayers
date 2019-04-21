# Keith's Layers (Klayers)

A collection of AWS Lambda Layers for Python3.7

# Status of layers

[![Updates](https://pyup.io/repos/github/keithrozario/Klayers/shield.svg)](https://pyup.io/repos/github/keithrozario/Klayers/)

If the layers are ever outdated, click the badge above for more info.

# Layer List

## Python Packages (in alphabetical order)

| Package        | ARN                                                                             | Version |        
| :------------- |:---------------------------------------------------------------------------     | ------- |
| aiohttp        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-aiohttp:5        | 5       |
| bcrypt         | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-bcrypt:3         | 3       |
| beautifulsoup4 | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-beautifulsoup4:4 | 4       |
| construct      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-construct:1      | 1       |
| elasticsearch  | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-elasticsearch:2  | 2       |
| ffmpeg-python  | arn:aws:lambda:**us-east-1**:113088814899:layer:Klayers-python37-ffmpeg-python:1| 1       |
| Pillow         | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-Pillow:5         | 5       |
| pymongo        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pymongo:1        | 1       |
| pyOpenSSL      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pyOpenSSL:3      | 3       |
| pytesseract    | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pytesseract:1    | 1       |
| requests       | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-requests:3       | 3       |
| spacy          | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-spacy:1          | 1       |
| tldextract     | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-tldextract:3     | 3       |


## Binaries

| Package        | ARN                                                                             | Version |        
| :------------- |:---------------------------------------------------------------------------     | ------- |
| tesseract      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers--tesseract:1              | 1       |

# Using the Layers

You can either:
* Set any of the ARNs above (for your region) to be a layer for your function. For list of all layers, view the `arns.json` file.
* Download the zip file from the directory of your package name in the packages directory (e.g. requests) and upload as a layer to your function

# Layer history

Whenever there is an new version of the underlying package, a new layer **may** be created with an incremented version number. View the changelog for each package.

# Building your own layer

To build a layer containing a single python package run the following in the packages directory:

    $ package.sh -p <package_name> -l <license> -r <runtime> -x <public/private> -a <aws_region>

e.g.

    $ package.sh -x public -a ap-southeast-1 -p requests -r python3.7 -l Apache-2.0
    $ package.sh -x private -a ap-southeast-1 -p beautifulsoup4 -r python3.7 -l MIT
    $ package.sh -p sqlite3 -r python3.7 -l Apache-2.0

* -p : (MANDATORY) Package Name
* -l : (MANDATORY) License information for the Package, use the SPDX license identifier
* -r : (MANDATORY) Runtime, currently only python3.7 is supported, but should work for python2.7 and python3.6
* -x : (OPTIONAL) set to public to make layer publicly accessible defaults to private
* -a : (OPTIONAL) aws regiondefaults to deploying layer in all aws_regions where lambda is available (except China)
* -b : (OPTIONAL) bypass flag to upload layers even if previous upload has the same hash

# Asking for more layers

Make a pull requests!

# Notes

All layers are deployed in every region (except China). Refer to the `arns.json` file for more info.

I intend to delete older layers after a while. Functions relying on deleted layers will still work after the layers are deleted. But you won't be able to create new functions referencing older layers.

# More notes

For `tldextract`, set the following environment variable to avoid trying to query the Mozilla tld file from the internet.

    $ TLDEXTRACT_CACHE=/opt/python/tldextract/.tld_set_snapshot

For `pytesseract`, the tesseract binary is not included in the build, but the layer includes Pillow. To use tesseract you'd need the tesseract binary layer as well.

For `spacy`, I had to manually tweak a few things to make the package fit into a layer, it only works for English, consider this beta. To use the included model:
    
    $ spacy.load('/opt/en_core_web_sm-2.1.0')

