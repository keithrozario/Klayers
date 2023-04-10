variable "app_name" { type = string }
variable "aws_region" { type = map(any) }
variable "aws_profile" { type = map(any) }
variable "lambda_prefix" { type = map(any) }
variable "github_repo" { type = string }
variable "api_domain_name" { type = map(any) }
variable "s3bucket_config_parameter_name_suffix" { type = string }
variable "github_role_name" { type = map(any) }