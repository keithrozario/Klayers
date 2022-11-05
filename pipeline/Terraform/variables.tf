variable "app_name" {}
variable "aws_region" { type = map(any) }
variable "aws_profile" { type = map(any) }
variable "lambda_prefix" { type = map(any) }
variable "github_repo" { type = string }
variable "api_domain_name" { type = map(any) }
variable "github_repo_role_name" { type = string }