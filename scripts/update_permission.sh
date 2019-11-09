#!/bin/bash

# I'm using a different AWS_PROFILE to upload my layers
export AWS_PROFILE=LayerUploader
LAYER_NAME=Klayers-python37-tesseract
LAYER_VERSION=1

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

for AWS_REGION in "${AWS_REGIONS[@]}"
do

	aws lambda add-layer-version-permission \
	--region $AWS_REGION \
	--layer-name $LAYER_NAME \
	--statement-id make_public_2 \
	--version-number $LAYER_VERSION \
	--principal '*' \
	--action lambda:GetLayerVersion

done