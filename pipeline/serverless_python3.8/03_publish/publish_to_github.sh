#@IgnoreInspection BashAddShebang
handler () {
    set -e

    SSH_KEY_DIR=/tmp/.ssh
    SSH_KEY_FILE=/tmp/.ssh/id_ecdsa
    KNOWN_HOSTS_FILE=/tmp/.ssh/known_hosts

    PACKAGE_DIR=deployments/python3.8/packages
    ARNS_DIR=deployments/python3.8/arns

    if [ ! -d $SSH_KEY_DIR ];
    then
        mkdir $SSH_KEY_DIR
    else
        rm -rf $SSH_KEY_DIR
        mkdir $SSH_KEY_DIR
    fi

    # Get keyfile
    aws ssm get-parameter --name $GITHUB_KEY --with-decryption  --output text --query Parameter.Value >> $SSH_KEY_FILE
    chmod 400 $SSH_KEY_FILE

    # Add github to known host file
    ssh-keyscan github.com >> /tmp/.ssh/known_hosts 2>&1

    # Setup ssh-agent
    eval `ssh-agent -s`
    ssh-add $SSH_KEY_FILE 2>&1

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

	rm -rf $ARNS_DIR && mkdir $ARNS_DIR
	aws s3 cp s3://$BUCKET_NAME/arns $ARNS_DIR --recursive

    rm -rf $PACKAGE_DIR && mkdir $PACKAGE_DIR
	aws s3 cp s3://$BUCKET_NAME/packages $PACKAGE_DIR --recursive

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
	rm -rf $SSH_KEY_DIR
    echo "{\"status\":\"done\"}" >&2
}