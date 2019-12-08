# Terraform Scripts for Deployment

This directory contains the terraform scripts for deployment, and the corresponding variables.

There are currently 3 workspaces:
* Klayers-default
* Klayers-dev
* Klayers-prod

All workspaces are configured for remote backends, hence all state files are stored on Terraform Cloud.

To switch to a new workspace:

    $ terraform workspace new Klayers-dev
    
The `new` is counterintuitive, but regardless of whether the workspace exists or not, the new keyword is required. Terraform will then load the state from Terraform cloud and all will be synced.

# Variables

All variables are stored in `terraform.tfvars.json`

# Note

The Key-Encrypting-Key for the GitHub SSH credentials is the only thing missing from terraform, this is added manually by:

* Uploading an aes-256-cbc encrypted SSH key named `github_id_rsa.enc` to the S3 keys bucket (note the name of the bucket is `s3bucket_keys`)
* Uploading the openssl password to /<app_name>/<workspace>/ssh_kek paramter in parameter store

This key is a deploy key for the repo in GitHub, and allows for both read/write access.

# Remote backend & workspaces

There is a known issue with remote backends and workspaces. To overcome this issue for free-tier users, you'll need to set the deployment type of the remote backend to `local` in order for the script to work. By default, all deployments on terraforms backend default to `remote` deployments which default all workspaces to `default`.

To change the deployment type to `local`, login to terraform.io, select the workspace. Go to setting, and set the deployment type to local.