# Terraform Scripts for Deployment

This directory contains the terraform scripts for deployment, and the corresponding variables.

There are currently 3 workspaces:

* Klayers-defaultp38
* Klayers-devp38
* Klayers-prodp38

All workspaces are configured for remote backends, hence all state files are stored on Terraform Cloud.

To switch to a new workspace:

    $terraform workspace new Klayers-dev

The `new` is counterintuitive, but regardless of whether the workspace exists or not, the new keyword is required. Terraform will then load the state from Terraform cloud and all will be synced.

## Variables

All variables are stored in `terraform.tfvars.json`

## Secrets

Due to the way Terraform manages the SSM Parameters, we've manually created and populated the secrets for Slack, Github (SSH Key) and Github Webhook secret into their own parameters:

* /kl/\<stage>/github_ssh_key
* /kl/\<stage>/github_webhook_secret
* /kl/\<stage>/slack_token

## Remote backend & workspaces

There is a known issue with remote backends and workspaces. To overcome this issue for free-tier users, you'll need to set the deployment type of the remote backend to `local` in order for the script to work. By default, all deployments on terraforms backend default to `remote` deployments which default all workspaces to `default`.

To change the deployment type to `local`, login to terraform.io, select the workspace. Go to setting, and set the deployment type to local.