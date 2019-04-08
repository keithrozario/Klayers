# Keith's Layers (Klayers)

A collection of AWS Lambda Layers for Python3.7

# Status of layers

[![Updates](https://pyup.io/repos/github/keithrozario/Klayers/shield.svg)](https://pyup.io/repos/github/keithrozario/Klayers/)

If the layers are ever outdated, click the badge above for more info.

# Layer List

## Python Packages

| Package        | ARN                                                                             | Version |        
| :------------- |:---------------------------------------------------------------------------     | ------- |
| requests       | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-requests:2       | 2       |
| beautifulsoup4 | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-beautifulsoup4:3 | 3       |
| elasticsearch  | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-elasticsearch:1  | 1       |
| bcrypt         | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-bcrypt:2         | 2       |
| pymongo        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pymongo:1        | 1       |
| pyOpenSSL      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pyOpenSSL:2      | 2       |
| aiohttp        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-aiohttp:5        | 5       |
| ffmpeg-python  | arn:aws:lambda:us-east-1:113088814899:layer:Klayers-python37-ffmpeg-python:1    | 1       |
| tldextract     | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-tldextract:1     | 1       |
| construct      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-construct:1      | 1       |
| Pillow         | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-Pillow:1         | 5       |
| pytesseract    | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pytesseract:1    | 1       |

## Binaries

| Package        | ARN                                                                             | Version |        
| :------------- |:---------------------------------------------------------------------------     | ------- |
| tesseract      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers--tesseract:1              | 1       |

# Using the Layers

You can either:
* Set any of the ARNs above (for your region) to be a layer for your function. For list of all layers, view the `arns.json` file.
* Download the zip file from the directory of your package name (e.g. requests) and upload as a layer to your function

# Layer history

Whenever there is an new version of the underlying package, a new layer **may** be created with an incremented version number. View the changelog for each package.

# Building your own layer

To build a layer containing a single python package use the following:

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

All layers are deployed in every region (except China). Refer to the arns.json file for more info.

I intend to delete older layers after a while. Functions relying on deleted layers will still work after the layers are deleted. But you won't be able to create new functions referencing older layers.

# More notes

For tldextract, set the following environment variable to avoid trying to query the Mozilla tld file from the internet.

    $ TLDEXTRACT_CACHE=/opt/python/tldextract/.tld_set_snapshot

For pytesseract, the tesseract binary is not included in the build, but the layer includes Pillow. To use tesseract you'd need the tesseract binary layer as well.

