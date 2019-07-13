variable "app_name" {}
variable "aws_region" { type = "map" }
variable "s3bucket_layers" { type = "map" }
variable "dynamodb_layers" { type="map" }
variable "dynamodb_requirements" { type="map" }
variable "aws_profile" { type="map" }
variable "lambda_prefix" { type="map" }

# Provider Block
provider "aws" {
  version    = "~> 2.7"
  profile = "${lookup(var.aws_profile, terraform.workspace)}"
  region     = "${lookup(var.aws_region, terraform.workspace)}"
}

# Infra Block

## DynamoDB Table
resource "aws_dynamodb_table" "dynamodb_layers" {

  name           = "${lookup(var.dynamodb_layers, terraform.workspace)}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "region"
  range_key      = "package-version"

  attribute {
    name = "region"
    type = "S"
  }

  attribute {
    name = "package-version"
    type = "S"
  }

}

resource "aws_dynamodb_table" "dynamodb_requirements" {

  name           = "${lookup(var.dynamodb_requirements, terraform.workspace)}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "package"
  range_key      = "version"

  attribute {
    name = "package"
    type = "S"
  }

  attribute {
    name = "version"
    type = "S"
  }

}

## S3 Bucket
resource "aws_s3_bucket" "s3bucket_layers" {
  bucket = "${lookup(var.s3bucket_layers, terraform.workspace)}"
  acl    = "private"
  force_destroy = false
}

### Outputs for serverless to consume
resource "aws_ssm_parameter" "dynamodb_layers_table" {
  type  = "String"
  description = "Name of DynamoDB Temp Table"
  name  = "/${var.app_name}/${terraform.workspace}/dynamodb_layers_table"
  value = "${aws_dynamodb_table.dynamodb_layers.name}"
  overwrite = true
}

resource "aws_ssm_parameter" "dynamodb_layers_table_arn" {
  type  = "String"
  description = "ARN of DynamoDB Temp Table"
  name  = "/${var.app_name}/${terraform.workspace}/dynamodb_layers_table_arn"
  value = "${aws_dynamodb_table.dynamodb_layers.arn}"
  overwrite = true
}

resource "aws_ssm_parameter" "dynamodb_requirements_table" {
  type  = "String"
  description = "Name of DynamoDB Temp Table"
  name  = "/${var.app_name}/${terraform.workspace}/dynamodb_requirements_table"
  value = "${aws_dynamodb_table.dynamodb_requirements.name}"
  overwrite = true
}

resource "aws_ssm_parameter" "dynamodb_requirements_table_arn" {
  type  = "String"
  description = "ARN of DynamoDB Temp Table"
  name  = "/${var.app_name}/${terraform.workspace}/dynamodb_requirements_table_arn"
  value = "${aws_dynamodb_table.dynamodb_requirements.arn}"
  overwrite = true
}


resource "aws_ssm_parameter" "s3bucket_layers" {
  type  = "String"
  name  = "/${var.app_name}/${terraform.workspace}/s3bucket_layers"
  value = "${aws_s3_bucket.s3bucket_layers.bucket}"
  overwrite = true
}

resource "aws_ssm_parameter" "s3bucket_layers_arn" {
  type  = "String"
  name  = "/${var.app_name}/${terraform.workspace}/s3bucket_layers_arn"
  value = "${aws_s3_bucket.s3bucket_layers.arn}"
  overwrite = true
}