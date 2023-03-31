REGION=ap-southeast-1
PROFILE=KlayersDev
STAGE=Klayers-defaultp38

REPO_URL=$(aws ssm get-parameter --name /kl/$STAGE/build/p39/x86/repo --profile $PROFILE --region $REGION | jq -r '.Parameter.Value')
aws ecr get-login-password --region $REGION --profile $PROFILE | docker login --username AWS --password-stdin $REPO_URL
docker build -t p39build .
docker tag p39build:latest $REPO_URL:latest
docker push $REPO_URL:latest

DIGEST=$(aws ecr describe-images --repository-name p39build --profile $PROFILE --region $REGION --filter tagStatus=TAGGED | jq -r '.imageDetails[0].imageDigest')
aws ssm put-parameter --name /kl/$STAGE/build/p39/x86/digest --value $DIGEST --profile $PROFILE --region $REGION --overwrite | jq '.'
