# Container Build Images
variable app_name{}
variable workspace_full_name{}
variable python_version{}
variable architecture{}

resource "aws_ecr_repository" "build" {
  name                 = "${var.python_version}${var.architecture}build"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ssm_parameter" "build" {
  type        = "String"
  description = "URL for ${var.python_version} ${var.architecture} repo"
  name        = "/${var.app_name}/${var.workspace_full_name}/build/${var.python_version}/${var.architecture}/repo"
  value       = aws_ecr_repository.build.repository_url
  overwrite   = true
}