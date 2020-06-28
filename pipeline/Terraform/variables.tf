variable "app_name" {}
variable "aws_region" {type = map}
variable "dynamodb_layers" { type = map }
variable "aws_profile" { type = map }
variable "lambda_prefix" { type = map }
variable "github_repo" { type = map }
variable "runtime" { type = map }