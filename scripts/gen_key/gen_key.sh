ssh-keygen -t ecdsa -a 500 -b 521 -C keith+klayersbot@keithrozario.com -f "id_ecdsa.pem"

aws ssm put-parameter \
        --region ap-southeast-1 \
        --name "/kl/Klayers-defaultp38/github_ssh_key" \
        --type SecureString \
        --description "GitHub Repo Key" \
        --value "$(cat id_ecdsa.pem)" \
        --profile KlayersDev