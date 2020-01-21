#!/usr/bin/env bash

ssh-keygen -t ecdsa -a 500 -b 521 -C keith+klayersbot@keithrozario.com -f "id_ecdsa.pem"

REGION=us-east-2
PARAMETER_NAME=github_ssh_key
STAGE=Klayers-prodp38
PROFILE=KlayersProdP38

aws ssm put-parameter \
        --region $REGION \
        --name "/kl/$STAGE/$PARAMETER_NAME" \
        --type SecureString \
        --description "GitHub Repo Key" \
        --value "$(cat id_ecdsa.pem)" \
        --profile $PROFILE \
        --overwrite