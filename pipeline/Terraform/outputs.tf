output "github_role_arn" {
  value = module.oidc_github.github_role_arn
}
output "config_bucket_name_parameter" {
  value = aws_ssm_parameter.config_bucket_name.name
}