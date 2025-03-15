# Container Build Images

## Python 3.11 - x86
resource "aws_ecr_repository" "p311build" {
  name                 = "p311build"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ssm_parameter" "p311_build_repo" {
  type        = "String"
  description = "URL for p311 arm64 repo"
  name        = "/${var.app_name}/${local.workspace_full_name}/build/p311/x86/repo"
  value       = aws_ecr_repository.p311build.repository_url
}

## Python 3.11 - arm64
resource "aws_ecr_repository" "p311build_arm64" {
  name                 = "p311armbuild"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ssm_parameter" "p311_arm64_build_repo" {
  type        = "String"
  description = "URL for p311 arm64 repo"
  name        = "/${var.app_name}/${local.workspace_full_name}/build/p311/arm64/repo"
  value       = aws_ecr_repository.p311build_arm64.repository_url
}


## Python 3.12 builds

module "python312_x86_build" {
  source             = "./container_repository"
  app_name           = var.app_name
  workspace_full_name = local.workspace_full_name
  python_version = "p312"
  architecture = "x86"
}

module "python312_arm64_build" {
  source             = "./container_repository"
  app_name           = var.app_name
  workspace_full_name = local.workspace_full_name
  python_version = "p312"
  architecture = "arm64"
}

## Python 3.13 builds

module "python313_x86_build" {
  source             = "./container_repository"
  app_name           = var.app_name
  workspace_full_name = local.workspace_full_name
  python_version = "p313"
  architecture = "x86"
}

module "python313_arm64_build" {
  source             = "./container_repository"
  app_name           = var.app_name
  workspace_full_name = local.workspace_full_name
  python_version = "p313"
  architecture = "arm64"
}