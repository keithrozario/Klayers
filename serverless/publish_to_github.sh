handler () {
    set -e
    cd /tmp
    git clone https://github.com/keithrozario/Klayers

    cd Klayers
    aws s3 cp s3://klayers-bucket--prod/packages packages --recursive
    aws s3 cp s3://klayers-bucket--prod/arns arns --recursive

    COMMITDATE=$(date +%x_%H:%M)
    git add -A
    git commit -m "$COMMITDATE"
    echo $COMMITDATE

    SSH_KEY=$(aws secretsmanager get-secret-value --secret-id /Klayers-python37/Klayers-prod/github_deploy_key | jq -r .SecretString | jq -r .sshkey)
    echo $SSH_KEY >> /tmp/.ssh_key
    chmod 400 /tmp/.ssh_key

    ls -lah /tmp

}