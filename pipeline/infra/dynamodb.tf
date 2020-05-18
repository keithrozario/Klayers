module "dynamo_table" {
  source              = "./dynamodb"
  table_logical_name = "db"
  app_name = lookup(var.app_name, terraform.workspace)
  workspace_name = terraform.workspace
}