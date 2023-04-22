#! /bin/bash

## First Argument to the script is the $STAGE, all other arguments are then taken from the configuration file
## e.g. $ ./deploy-container.sh Klayers-defaultp38

STAGE="${1:-Klayers-defaultp38}"
REGION=$(cat ../../../Terraform/terraform.tfvars.json | jq -r --arg STAGE $STAGE '.aws_region."\($STAGE)"')
PROFILE=$(cat ../../../Terraform/terraform.tfvars.json | jq -r --arg STAGE $STAGE '.aws_profile."\($STAGE)"')
PARAM_PREFIX=build/p39/x86
REPO_PARAM=/kl/$STAGE/$PARAM_PREFIX/repo

REPO_URL=$(aws ssm get-parameter --name $REPO_PARAM  --profile $PROFILE --region $REGION | jq -r '.Parameter.Value')
REPO_NAME=$(echo $REPO_URL | cut -d'/' -f2)

aws ecr get-login-password --region $REGION --profile $PROFILE | docker login --username AWS --password-stdin $REPO_URL
docker build -t $REPO_NAME .
docker tag $REPO_NAME:latest $REPO_URL:latest
docker push $REPO_URL:latest

DIGEST=$(aws ecr describe-images --repository-name $REPO_NAME --profile $PROFILE --region $REGION --image-ids imageTag=latest | jq -r '.imageDetails[0].imageDigest')
aws ssm put-parameter --name /kl/$STAGE/$PARAM_PREFIX/digest --value $DIGEST --profile $PROFILE --region $REGION --overwrite --type String | jq '.'
