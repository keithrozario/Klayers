terraform {
  required_version = ">= 0.12.0"

  backend "remote" {
    organization = "keithrozario"

    workspaces {
      prefix = "Klayers-"
    }
  }
}

# Provider Block
provider "aws" {
  version = "~> 2.7"
  profile = lookup(var.aws_profile, terraform.workspace)
  region  = lookup(var.aws_region, terraform.workspace)
}

module "dynamo_table" {
  source              = "./dynamodb"
  table_logical_name = "db"
  app_name = lookup(var.app_name, terraform.workspace)
  workspace_name = terraform.workspace
}

# High level parameters
resource "aws_ssm_parameter" "lambda_prefix" {
  type      = "String"
  name      = "/${lookup(var.app_name, terraform.workspace)}/${terraform.workspace}/lambda_prefix"
  value     = lookup(var.lambda_prefix, terraform.workspace)
  overwrite = true
}

resource "aws_ssm_parameter" "github_repo" {
  type      = "String"
  name      = "/${lookup(var.app_name, terraform.workspace)}/${terraform.workspace}/github_repo"
  value     = lookup(var.github_repo, terraform.workspace)
  overwrite = true
}