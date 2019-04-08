#!/bin/bash
# 
# File: package.sh
# Description: Builds and Deploys a single python package (e.g. requests) as an AWS Lambda Layer
#
# Author: Keith Rozario <keith@keithrozario.com>
# 
# Usage: ./package.sh -p package_name -r runtime -l license
#        -p : Name of python package (e.g. requests)
#        -r : Compatible Runtimes for the Layer (e.g. python3.6, python3.7)
#        -l : License (e.g. Apache-2.0, MIT) in SPIX
#        -x : permission of layer, defaults to private, set -x to public to make layer publicly accessible
#        -a : aws region to deploy to, defaults to ALL regions
#        -b : bypass duplicate checks, uploads new version all the time
#
# Examples:
# Deploy requests package to public available layer to all aws regions:
# ./package.sh -x public -a ap-southeast-1 -p requests -r python3.7 -l Apache-2.0
# 
# Deploy beautifulsoup4 package to private layer in ap-southeast-1:
# ./package.sh -a ap-southeast-1 -p beautifulsoup4 -r python3.7 -l MIT
#
# Tested on: GNU bash, version 3.2.57(1)-release (x86_64-apple-darwin18)
#            aws-cli/1.16.81 Python/2.7.15 Darwin/18.2.0 botocore/1.12.73
#.           LibreSSL 2.6.5
#
# Depedencies: openssl (used to hash the requirements.txt file)
# 			   python (build with python3.6 or python3.7 not python3)
#			   aws-cli
#			   

LOG_FILE="$(date '+%d-%m-%y')_log.txt"

while getopts ":p:d:l:a:x:b:" arg; do
  case $arg in
    p) PACKAGE=$OPTARG;;  # Name of the package
	d) ZIPPATH=$OPTARG;;  # path to package
    l) LAYER_LICENSE=$OPTARG;;  # License of package in SPIX 
    a) AWS_REGION=$OPTARG;;
	x) PUBLIC=$OPTARG;;
	b) BYPASS=$OPTARG;;
   \?) echo "Invalid option: -$OPTARG" >&2
       exit 1;;
  esac
done

# Check if all parameters provided
if [ -z "$PACKAGE" ] || [ -z "$LAYER_LICENSE" ]
then
	echo "All variables -p <package_name> -l <license> must be provided"
	exit 1
else 
	printf "Layer Package : $PACKAGE\n" 2>&1 | tee -a "$LOG_FILE"
	printf "Layer License : $LAYER_LICENSE\n" 2>&1 | tee -a "$LOG_FILE"

	if [ "$PUBLIC" = public ]
	then
		printf "INFO: Layer will be made public!\n" 2>&1 | tee -a "$LOG_FILE"
	else
		printf "Layer will be Private\n" 2>&1 | tee -a "$LOG_FILE"
	fi

	if [ -z "$AWS_REGION" ]
	then
		printf "INFO: Deploying to all regions!\n" 2>&1 | tee -a "$LOG_FILE"
		# China not included as I'm unable to deploy there
		AWS_REGIONS=( ap-northeast-1 ap-northeast-2
			ap-south-1
			ap-southeast-1 ap-southeast-2
			ca-central-1
			eu-central-1
			eu-north-1
			eu-west-1 eu-west-2 eu-west-3
			sa-east-1
			us-east-1 us-east-2
			us-west-1 us-west-2
			)
	else
		printf "INFO: Deploying to $AWS_REGION\n" 2>&1 | tee -a "$LOG_FILE"
		AWS_REGIONS=( $AWS_REGION )
	fi
fi

# I'm using a different AWS_PROFILE to upload my layers
export AWS_PROFILE=LayerUploader

LAYER_PREFIX=Klayers-
LAYER_NAME=$LAYER_PREFIX-$PACKAGE
LAYER_DESC="Lambda Layer with $PACKAGE"

# Calculate hash of requirements.txt file
function sha256sum() { openssl sha256 "$@" | awk '{print $2}'; }
NEW_SHA256=$(sha256sum $ZIPPATH | xxd -r -p | base64)  # Take the sha, hexlify, and then base64
printf "New Hash: ${NEW_SHA256}\n" 2>&1 | tee -a "$LOG_FILE"


for AWS_REGION in "${AWS_REGIONS[@]}"
do

	# Get hash of latest version
	LIST_LAYERS=$(aws lambda list-layer-versions --layer-name $LAYER_NAME --region $AWS_REGION)
	LAYER_VERSION=$(jq -r '.LayerVersions[0].Version' <<< "${LIST_LAYERS}")
	printf "Latest version in $AWS_REGION: ${LAYER_VERSION}\n" 2>&1 | tee -a "$LOG_FILE"

	if [ $LAYER_VERSION = "null" ]  # JQ will set value to null if unable to get the key
	then
		printf "No previous version found in $AWS_REGION. Proceeding to upload\n" 2>&1 | tee -a "$LOG_FILE"
		LAYER_VERSION=1
		LAYER_SHA256="dummy"
	else
		GET_LAYER=$(aws lambda get-layer-version --version-number ${LAYER_VERSION} --layer-name $LAYER_NAME --region $AWS_REGION)
		LAYER_SHA256=$(jq -r '.CodeSha256' <<< "${GET_LAYER}")
		printf "Old Hash: ${LAYER_SHA256}\n" 2>&1 | tee -a "$LOG_FILE"
		# increment version
		let "LAYER_VERSION++"
	fi

	# not the ideal, but let me explain ... I was too lazy
	if [[ $* == *-b* ]]
	then
		printf "Bypass flag detected, uploading files even if hashes match"
		LAYER_SHA256="dummy"
	fi

	if [ $NEW_SHA256 = $LAYER_SHA256 ]
	then
		printf "Hashes match everything is up to date, bypassing upload\n\n"
	else
		printf "########################\n\n" >> "$LOG_FILE"
		printf "Deploying to $AWS_REGION\n" 2>&1 | tee -a "$LOG_FILE"

		# deploy -- description is of format $LAYER_DESC |$REQTXT_SHA256
		aws lambda publish-layer-version \
		--region $AWS_REGION \
		--layer-name $LAYER_NAME \
		--zip-file fileb://$ZIPPATH \
		--compatible-runtimes $LAYER_RUNTIME \
		--license-info $LAYER_LICENSE | jq '.' 2>&1 | tee -a "$LOG_FILE"

		if [ -z $PUBLIC ]
		then
			printf "Layer Set to Private\n" 2>&1 | tee -a "$LOG_FILE"
		else
			printf "Updating Policy to make version $LAYER_NAME:$LAYER_VERSION Public\n" 2>&1 | tee -a "$LOG_FILE"
			aws lambda add-layer-version-permission \
			--region $AWS_REGION \
			--layer-name $LAYER_NAME \
			--statement-id make_public \
			--version-number $LAYER_VERSION \
			--principal '*' \
			--action lambda:GetLayerVersion | jq '.' 2>&1 | tee -a "$LOG_FILE"
		fi

	fi
done
