#@IgnoreInspection BashAddShebang
handler () {
    set -e

    SSH_KEY_DIR=/tmp/.ssh
    KNOWN_HOSTS_FILE=/tmp/.ssh/known_hosts

    if [ ! -d $SSH_KEY_DIR ];
    then
        mkdir $SSH_KEY_DIR
    else
        rm -rf $SSH_KEY_DIR
        mkdir $SSH_KEY_DIR
    fi

    # Get encrypted key file
    aws s3 cp s3://$S3_KEYS/github_id_rsa.enc /tmp/.ssh/github_id_rsa.enc

    # get key encrypting key
    KEK_SSM_RESPONSE=$(aws ssm get-parameter --name $KEK_PARAMETER)
    KEK=$(jq -r '.Parameter.Value' <<< "${KEK_SSM_RESPONSE}")
    openssl aes-256-cbc -d -in /tmp/.ssh/github_id_rsa.enc -out /tmp/.ssh/github_id_rsa -k $KEK -md sha256
    chmod 400 /tmp/.ssh/github_id_rsa

    # Add github to known host file
    ssh-keyscan github.com >> /tmp/.ssh/known_hosts 2>&1

    # Setup ssh-agent
    eval `ssh-agent -s`
    ssh-add /tmp/.ssh/github_id_rsa 2>&1

    # Point git to known hosts and key files
    export GIT_SSH="/tmp"
    export GIT_SSH_COMMAND="ssh -o UserKnownHostsFile=/tmp/.ssh/known_hosts -i /tmp/.ssh/github_id_rsa"

    # Clone the repo
    cd /tmp
    REPO_NAME=$(echo $GITHUB_REPO | cut -d'/' -f2 | cut -d'.' -f1)
    if [ -d $$REPO_NAME ];
    then
        rm -rf $SSH_KEY_DIR
    fi

    if [ -d $REPO_NAME ];
    then
        echo "found previous copy of repo, deleting..."
        rm -rf $REPO_NAME 
    else
        echo "No previous repo clones found"
    fi

    git clone $GITHUB_REPO
    cd $REPO_NAME

    # Set github user
    echo "[user]
	    email = keith+klayersbot@keithrozario.com
	    name = klayersbot" >> /tmp/$REPO_NAME/.git/config

	# Checkout and push
	cd /tmp/$REPO_NAME
	aws s3 cp s3://$BUCKET_NAME/arns deployments/python3.8/arns --recursive
	aws s3 cp s3://$BUCKET_NAME/packages deployments/python3.8/packages --recursive
	git add -A

	if [ -n "$(git status --porcelain)" ];
    then
        COMMITDATE=$(date +%x_%H:%M)
        git commit -m "$COMMITDATE"
	    git push
	else
      echo "No changes in Repo"
    fi

	# delete ssh key from execution context!!
	rm -rf /tmp/.ssh/
    echo "Done" >&2
}