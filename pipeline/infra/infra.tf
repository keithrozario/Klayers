variable "app_name" {}
variable "aws_region" {type = map}
variable "dynamodb_layers" { type = map }
variable "dynamodb_requirements" { type = map }
variable "aws_profile" { type = map }
variable "lambda_prefix" { type = map }
variable "github_repo" { type = map }
variable "runtime" { type = map }

terraform {
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

# Infra Block

## DynamoDB Table
resource "aws_dynamodb_table" "dynamodb_layers" {

  name             = lookup(var.dynamodb_layers, terraform.workspace)
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "deployed_region-package" # use . as separator e.g. us-east-1.requests
  range_key        = "layer_version"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "deployed_region-package"
    type = "S"
  }

  attribute {
    name = "layer_version"
    type = "N"
  }

  attribute {
    name = "deployed_region" # region is a DynamoDB reserved keyword
    type = "S"
  }

  attribute {
    name = "created_date"
    type = "S"
  }

  ttl {
    attribute_name = "time_to_live"
    enabled        = true
  }

  global_secondary_index {
    name            = "LayersPerRegion"
    hash_key        = "deployed_region"
    range_key       = "created_date"
    projection_type = "INCLUDE"
    non_key_attributes = ["package_version", "time_to_live", "package",
    "layer_version_arn", "layer_version", "created_date", ]
    # Terraform has an issue where non_key_attributes of GSI must be in **some** order
    # refer here: https://github.com/terraform-providers/terraform-provider-aws/issues/3828
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "db_layers"
    Environment = terraform.workspace
  }

}


### Outputs for serverless to consume
resource "aws_ssm_parameter" "dynamodb_layers_table" {
  type        = "String"
  description = "Name of DynamoDB Layers Table"
  name        = "/${lookup(var.app_name, terraform.workspace)}/${terraform.workspace}/dynamodb_layers_table"
  value       = aws_dynamodb_table.dynamodb_layers.name
  overwrite   = true
}

resource "aws_ssm_parameter" "dynamodb_layers_table_arn" {
  type        = "String"
  description = "ARN of DynamoDB Layers Table"
  name        = "/${lookup(var.app_name, terraform.workspace)}/${terraform.workspace}/dynamodb_layers_table_arn"
  value       = aws_dynamodb_table.dynamodb_layers.arn
  overwrite   = true
}

resource "aws_ssm_parameter" "dynamodb_layers_stream_arn" {
  type        = "String"
  description = "ARN of DynamoDB Layers Table Stream"
  name        = "/${lookup(var.app_name, terraform.workspace)}/${terraform.workspace}/dynamodb_layers_stream_arn"
  value       = aws_dynamodb_table.dynamodb_layers.stream_arn
  overwrite   = true
}

resource "aws_ssm_parameter" "dynamodb_layers_stream_lable" {
  type        = "String"
  description = "Lable of DynamoDB Layers Table Stream"
  name        = "/${lookup(var.app_name, terraform.workspace)}/${terraform.workspace}/dynamodb_layers_stream_lable"
  value       = aws_dynamodb_table.dynamodb_layers.stream_label
  overwrite   = true
}

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

# resource "aws_ssm_parameter" "github_webhook_secret" {
#   type      = "SecureString"
#   name      = "/${lookup(var.app_name, terraform.workspace)}/${terraform.workspace}/github_webhook_secret"
#   value = "to be modified"
#   overwrite = false
# }
