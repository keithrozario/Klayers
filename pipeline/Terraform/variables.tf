variable "app_name" {}
variable "aws_region" { type = map(any) }
variable "aws_profile" { type = map(any) }
variable "lambda_prefix" { type = map(any) }
variable "github_repo" { type = map(any) }
variable "api_domain_name" { type = map(any) }