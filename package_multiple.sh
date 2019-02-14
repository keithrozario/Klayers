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
#        -l : License (e.g. Apache-2.0, MIT)
#        -x : permission of layer, defaults to private, set -x to public to make layer publicly accessible
#        -a : aws region to deploy to, defaults to ALL regions
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

while getopts ":p:r:l:a:x:n:" arg; do
  case $arg in
    p) PACKAGE_FILE=$OPTARG;;  # Name of the python package to install
    r) LAYER_RUNTIME=$OPTARG;;  # Runtime version e.g. python3.7
    l) LAYER_LICENSE=$OPTARG;;  # License of package in SPIX 
    a) AWS_REGION=$OPTARG;;
	x) PUBLIC=$OPTARG;;
	n) PACKAGE_NAME=$OPTARG;;
   \?) echo "Invalid option: -$OPTARG" >&2
       exit 1;;
  esac
done
PACKAGE="$PACKAGE_NAME"
PACKAGES=( $(cat "./$PACKAGE_FILE") )

# Check if all parameters provided
if [ -z "$PACKAGES" ] || [ -z "$LAYER_RUNTIME" ] || [ -z "$LAYER_LICENSE" ]
then
	echo "All variables -p <package_name> -r <runtime> -l <license> must be provided"
	exit 1
else 
	printf "Layer Package : $PACKAGES\n" 2>&1 | tee -a "$LOG_FILE"
	printf "Layer Runtime : $LAYER_RUNTIME\n" 2>&1 | tee -a "$LOG_FILE"
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
LAYER_RUNTIME_NODOT="${LAYER_RUNTIME//.}"  # removes . between 3.7
ZIP_NAME=$LAYER_PREFIX$LAYER_RUNTIME_NODOT-$PACKAGE.zip
LAYER_NAME=$LAYER_PREFIX$LAYER_RUNTIME_NODOT-$PACKAGE
LAYER_DESC="Lambda Layer with $PACKAGE"
export PKG_DIR="python"
export DOCKER_IMAGE="lambci/lambda:build-$LAYER_RUNTIME"

# Setup Log File
printf "########################\n" >> "$LOG_FILE"
date >> "$LOG_FILE"
printf "\n" >> "$LOG_FILE"
printf "########################\n" >> "$LOG_FILE"

# Create new virtualenv and install latest version of package into it
printf "Creating new virtualenv\n" 
$LAYER_RUNTIME -m venv venv/
source venv/bin/activate
pip install --upgrade pip >> "$LOG_FILE"
for i in ${PACKAGES[@]}; do  # install all packages in $PACKAGES array
	printf "Pip-Installing $i into virtualenv\n"
	pip install -q $i >> "$LOG_FILE"
done
pip freeze > requirements.txt
# there will be conflict with the typing library for python3.7 lambda, have to remove
sed '/^typing/d' requirements.txt > temp.txt && mv temp.txt requirements.txt
deactivate
rm -rf venv/ # don't need the virtualenv anymore

# log requirements,txt
printf "requirements.txt########\n\n" >> "$LOG_FILE"
cat requirements.txt >> "$LOG_FILE"
printf "\n########################\n" >> "$LOG_FILE"

# Build docker package
printf "Packing in Docker\n"
rm -rf ${PKG_DIR} && mkdir -p ${PKG_DIR}
docker run --rm -v $(pwd):/foo -w /foo ${DOCKER_IMAGE} \
pip install -q -r requirements.txt -t ${PKG_DIR} >> "$LOG_FILE"

if [ -f $ZIP_NAME ]
then
	printf "Deleting previous zip file version\n" 2>&1 | tee -a "$LOG_FILE"
	rm $ZIP_NAME
else
	: # do nothing
fi
printf "Zipping up build package\n" 2>&1 | tee -a "$LOG_FILE"
cp requirements.txt ${PKG_DIR}
zip -r $ZIP_NAME ${PKG_DIR} >> "$LOG_FILE"
rm -rf ${PKG_DIR}

# Calculate hash of requirements.txt file
function sha256sum() { openssl sha256 "$@" | awk '{print $2}'; }
REQTXT_SHA256=$(sha256sum requirements.txt | xxd -r -p | base64)  # Take the sha, hexlify, and then base64
printf "New Requirements.txt Hash: ${REQTXT_SHA256}\n" 2>&1 | tee -a "$LOG_FILE"


for AWS_REGION in "${AWS_REGIONS[@]}"
do

	# Get hash of latest version
	LIST_LAYERS=$(aws lambda list-layer-versions --compatible-runtime $LAYER_RUNTIME --layer-name $LAYER_NAME --region $AWS_REGION)
	LAYER_VERSION=$(jq -r '.LayerVersions[0].Version' <<< "${LIST_LAYERS}")
	printf "Latest version in $AWS_REGION: ${LAYER_VERSION}\n" 2>&1 | tee -a "$LOG_FILE"

	if [ $LAYER_VERSION = "null" ]  # JQ will set value to null if unable to get the key
	then
		printf "No previous version found in $AWS_REGION. Proceeding to upload\n" 2>&1 | tee -a "$LOG_FILE"
		LAYER_REQTXT_SHA256="dummy"  #dummy so won't match SHA256
		LAYER_VERSION=1
	else
		GET_LAYER=$(aws lambda get-layer-version --version-number ${LAYER_VERSION} --layer-name $LAYER_NAME --region $AWS_REGION)
		GET_LAYER_DESC=$(jq -r '.Description' <<< "${GET_LAYER}")
		LAYER_REQTXT_SHA256=$(echo "${GET_LAYER_DESC}" | cut -d "|" -f 2)  # I include the SHA256 of requirements.txt into the description
		printf "Old Requirements.txt Hash: ${LAYER_REQTXT_SHA256}\n" 2>&1 | tee -a "$LOG_FILE"
		# increment version
		let "LAYER_VERSION++"
	fi

	if [ $REQTXT_SHA256 = $LAYER_REQTXT_SHA256 ]
	then
		printf "Hashes match everything is up to date, bypassing upload\n\n"
	else
		printf "########################\n\n" >> "$LOG_FILE"
		printf "Deploying to $AWS_REGION\n" 2>&1 | tee -a "$LOG_FILE"

		# deploy -- description is of format $LAYER_DESC |$REQTXT_SHA256
		aws lambda publish-layer-version \
		--region $AWS_REGION \
		--layer-name $LAYER_NAME \
		--zip-file fileb://$ZIP_NAME \
		--description "$LAYER_DESC |$REQTXT_SHA256" \
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

		# Store deployment artifacts
		CHANGE_DIR=changelog
		LATEST_DIR=latest
		if [ -d $PACKAGE ]
		then
			:
		else
			mkdir $PACKAGE
			mkdir $PACKAGE/$CHANGE_DIR
			mkdir $PACKAGE/$LATEST_DIR
		fi

		cp $ZIP_NAME $PACKAGE/$LATEST_DIR # ensure latest package is stored in repo
		cp requirements.txt $PACKAGE/$LATEST_DIR  # ensure latest requirements.txt is stored in repo for scanning
		cp $PACKAGE/$LATEST_DIR/requirements.txt $PACKAGE/$CHANGE_DIR/v$LAYER_VERSION.$AWS_REGION.requirements.txt

	fi
done

# Remove left-over files
rm $ZIP_NAME
rm requirements.txt
