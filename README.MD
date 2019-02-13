# Keith's Layers (Klayers)

A collection of AWS Lambda Layers for Python3.7

# Status of layers

[![Updates](https://pyup.io/repos/github/keithrozario/Klayers/shield.svg)](https://pyup.io/repos/github/keithrozario/Klayers/)

If the layers are ever outdated, click the badge above for more info.

# Layer List

| Package        | ARN                                                                             | Version |        
| :------------- |:---------------------------------------------------------------------------     | ------- |
| requests       | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-requests:1       | 1       |
| beautifulsoup4 | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-beautifulsoup4:2 | 2       |
| sqlite3        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-sqlite3:1        | 1       |
| elasticsearch  | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-elasticsearch:1  | 1       |
| bcrypt         | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-bcrypt:1         | 1       |
| pymongo        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pymongo:1        | 1       |
| pyOpenSSL      | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pyOpenSSL:1      | 1       |
| aiohttp        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pyaiohttp:1      | 1       |


# Using the Layers

You can either:
* Set any of the ARNs above (for your region) to be a layer for your function. For list of all layers, view the `arns.json` file.
* Download the zip file from the directory of your package name (e.g. requests) and upload as a layer to your function

# Layer history

Whenever there is an new version of the underlying package, a new layer will be created with an incremented version number.View the changelog for each package.

# Building your own layer

To build a layer containing a single python package use the following:

    $ package.sh -p <package_name> -l <license> -r <runtime> -x <public/private> -a <aws_region>

To buils a layer containing multiple python packages use the following:

	$ ./package_multiple.sh <path_to_textfile_with_package_list> -l <license> -r <runtime> -x <public/private> -a <aws_region> -n <package_name>

e.g.

    $ package.sh -x public -a ap-southeast-1 -p requests -r python3.7 -l Apache-2.0
    $ package.sh -x private -a ap-southeast-1 -p beautifulsoup4 -r python3.7 -l MIT
    $ package.sh -p sqlite3 -r python3.7 -l Apache-2.0
    $ package_multiple.sh -p aiohttp.txt -l Apache-2.0 -r python3.7 -x public -n aiohttp

* -p : (MANDATORY) Package Name
* -l : (MANDATORY) License information for the Package, use the SPDX license identifier
* -r : (MANDATORY) Runtime, currently only python3.7 is supported, but should work for python2.7 and python3.6
* -x : (OPTIONAL) set to public to make layer publicly accessible defaults to private
* -a : (OPTIONAL) and defaults to deploying layer in all aws_regions where lambda is available (except China)

# Asking for more layers

Make a pull requests!
