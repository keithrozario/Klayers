# Keith's Layers (Klayers)

A collection of AWS Lambda Layers for Python3.7

# Layer List

| Package        | ARN                                                                             |          
| :------------- |:---------------------------------------------------------------------------     |
| requests       | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-requests:1       |
| beautifulsoup4 | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-beautifulsoup4:1 |
| sqlite3        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-sqlite3:1        |      
| elasticsearch  | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-elasticsearch:1  |
| bcrypt         | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-bcrypt:1         |
| pymongo        | arn:aws:lambda:\<*region*>:113088814899:layer:Klayers-python37-pymongo:1        |

# Using the Layers

You can either:
* Set any of the ARNs above (for your region) to be a layer for your function. For list of all layers, view the `arns.json` file.
* Download the zip file from the directory of your package name (e.g. requests) and upload as a layer to your function

# Layer history

Whenever there is an new version of the underlying package, a new layer will be created with an incremented version number.View the changelog for each package.

# Building your own layer

Script only supports building stand-alone python packages (like requests and beautifulsoup4). While it can build wrappers, it will not be the underlying component that is wrapped.

To build a layer containing the python package abc use the following:

    $ package.sh -p <package_name> -l <license> -r <runtime> -x <public/private> -a <aws_region>

e.g.

    $ package.sh -x public -a ap-southeast-1 -p requests -r python3.7 -l Apache-2.0
    $ package.sh -x private -a ap-southeast-1 -p beautifulsoup4 -r python3.7 -l MIT
    $ package.sh -p sqlite3 -r python3.7 -l Apache-2.0

* -p : (MANDATORY) Package Name
* -l : (MANDATORY) License information for the Package, use the SPDX license identifier
* -r : (MANDATORY) Runtime, currently only python3.7 is supported, but should work for python2.7 and python3.6
* -x : (OPTIONAL) set to public to make layer publicly accessible defaults to private
* -a : (OPTIONAL) and defaults to deploying layer in all aws_regions where lambda is available (except China)

# Asking for more layers

Make a pull requests!
