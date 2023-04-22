#! /bin/bash

## First Argument to the script is the $STAGE, all other arguments are then taken from the configuration file
## e.g. $ ./deploy-container.sh Klayers-defaultp38

STAGE="${1:-Klayers-defaultp38}"
REGION=$(cat ../../../Terraform/terraform.tfvars.json | jq -r --arg STAGE $STAGE '.aws_region."\($STAGE)"')
PARAM_PREFIX=build/p310/x86
REPO_PARAM=/kl/$STAGE/$PARAM_PREFIX/repo

REPO_URL=$(aws ssm get-parameter --name $REPO_PARAM --region $REGION | jq -r '.Parameter.Value')
REPO_NAME=$(echo $REPO_URL | cut -d'/' -f2)

docker build -t $REPO_NAME .
docker tag $REPO_NAME:latest $REPO_URL:latest
docker push $REPO_URL:latest

DIGEST=$(aws ecr describe-images --repository-name $REPO_NAME --region $REGION --image-ids imageTag=latest | jq -r '.imageDetails[0].imageDigest')
aws ssm put-parameter --name /kl/$STAGE/$PARAM_PREFIX/digest --value $DIGEST --region $REGION --overwrite --type String | jq '.'
