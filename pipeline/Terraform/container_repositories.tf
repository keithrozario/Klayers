# Container Build Images

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

## Python 3.14 builds

module "python314_x86_build" {
  source             = "./container_repository"
  app_name           = var.app_name
  workspace_full_name = local.workspace_full_name
  python_version = "p314"
  architecture = "x86"
}

module "python314_arm64_build" {
  source             = "./container_repository"
  app_name           = var.app_name
  workspace_full_name = local.workspace_full_name
  python_version = "p314"
  architecture = "arm64"
}
