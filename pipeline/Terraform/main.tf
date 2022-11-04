terraform {
  required_version = ">= 0.12.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }

  backend "remote" {
    organization = "keithrozario"

    workspaces {
      prefix = "Klayers-"
    }
  }

}

locals {
  workspace_full_name = "Klayers-${terraform.workspace}"
}

# Provider Block
provider "aws" {
  profile = lookup(var.aws_profile, local.workspace_full_name)
  region  = lookup(var.aws_region, local.workspace_full_name)
}

provider "aws" {
  profile = lookup(var.aws_profile, local.workspace_full_name)
  region  = "us-east-1"
  alias   = "cloudfront"
}

module "dynamo_table" {
  source             = "./dynamodb"
  table_logical_name = "db"
  app_name           = lookup(var.app_name, local.workspace_full_name)
  workspace_name     = local.workspace_full_name
}

module "dynamo_table_ver_2" {
  source             = "./dynamodb"
  table_logical_name = "db-ver2"
  app_name           = lookup(var.app_name, local.workspace_full_name)
  workspace_name     = local.workspace_full_name
}

module "certificate" {
  source          = "./certificate_manager"
  api_domain_name = lookup(var.api_domain_name, local.workspace_full_name)
  app_name        = lookup(var.app_name, local.workspace_full_name)
  workspace_name  = local.workspace_full_name

  providers = {
    aws = aws.cloudfront
  }

}

# High level parameters

# Remove this layer in next version...
resource "aws_ssm_parameter" "lambda_prefix" {
  type      = "String"
  name      = "/${lookup(var.app_name, local.workspace_full_name)}/${local.workspace_full_name}/lambda_prefix"
  value     = lookup(var.lambda_prefix, local.workspace_full_name)
  overwrite = true
}

resource "aws_ssm_parameter" "github_repo" {
  type      = "String"
  name      = "/${lookup(var.app_name, local.workspace_full_name)}/${local.workspace_full_name}/github_repo"
  value     = lookup(var.github_repo, local.workspace_full_name)
  overwrite = true
}

resource "aws_ssm_parameter" "api_domain_name" {
  type      = "String"
  name      = "/${lookup(var.app_name, local.workspace_full_name)}/${local.workspace_full_name}/api/domain_name"
  value     = lookup(var.api_domain_name, local.workspace_full_name)
  overwrite = true
}

resource "aws_ssm_parameter" "cert_arn" {
  type        = "String"
  description = "Certificate Arn"
  name        = "/${lookup(var.app_name, local.workspace_full_name)}/${local.workspace_full_name}/api/cert/arn"
  value       = module.certificate.cert_arn
  overwrite   = true
}

## OIDC Block

module "oidc_github" {
  source             = "./oidc_github"
  app_name           = lookup(var.app_name, local.workspace_full_name)
  github_org         = split("/", split(":", var.github_repo)[1])[0]
  github_repo_name   = split(".", split(":", var.github_repo)[1])[0]
  config_bucket_arn  = aws_s3_bucket.s3bucket_config.arn
}