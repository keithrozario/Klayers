resource "aws_dynamodb_table" "t" {

  name             = "${var.app_name}.${var.workspace_name}.${var.table_logical_name}"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "pk"
  range_key        = "sk"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"
  
  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  attribute {
    name = "rgn"
    type = "S"
  }

  attribute {
    name = "dplySts"
    type = "S"
  }
  attribute {
    name = "pckg"
    type = "S"
  }

  attribute {
    name = "rqrmntsHsh"
    type = "S"
  }

  attribute {
    name = "rgn#PyVrsn"
    type = "S"
  }

  attribute {
    name = "pckg#PyVrsn"
    type = "S"
  }

  ttl {
    attribute_name = "exDt"
    enabled        = true
  }


  # for GSI in Terraform order of non_key_attributes need to match console
  # https://github.com/terraform-providers/terraform-provider-aws/issues/3828#issuecomment-522197376
  # This index to be removed on next release
  global_secondary_index {
    name            = "deployed_in_region"
    hash_key        = "rgn"
    range_key       = "dplySts"
    projection_type = "INCLUDE"
    non_key_attributes = ["exDt","crtdDt", "pckg", "pckgVrsn", "arn"]
  }

  global_secondary_index {
    name            = "deployed_in_region_by_python_version"
    hash_key        = "rgn#PyVrsn"
    range_key       = "dplySts"
    projection_type = "INCLUDE"
    non_key_attributes = ["exDt","crtdDt", "pckg", "pckgVrsn", "arn"]
  }

  # This index to be removed on next release
  global_secondary_index {
    name            = "package_global"
    hash_key        = "pckg"
    range_key       = "dplySts"
    projection_type = "INCLUDE"
    non_key_attributes = ["rgn", "rqrmntsHsh"]
  }

  global_secondary_index {
    name            = "package_global_by_python_version"
    hash_key        = "pckg#PyVrsn"
    range_key       = "dplySts"
    projection_type = "INCLUDE"
    non_key_attributes = ["rgn", "rqrmntsHsh"]
  }

  global_secondary_index {
    name            = "requirements_hash"
    hash_key        = "rqrmntsHsh"
    projection_type = "INCLUDE"
    non_key_attributes = ["rqrmntsTxt"]
  }


  tags = {
    Environment = var.workspace_name
  }

}

resource "aws_ssm_parameter" "table_name" {
  type        = "String"
  description = "Name of DynamoDB Table"
  name  = "/${var.app_name}/${var.workspace_name}/${var.table_logical_name}/name"
  value = aws_dynamodb_table.t.id
}

resource "aws_ssm_parameter" "table_arn" {
  type  = "String"
  description = "Arn of DynamoDB Table"
  name  = "/${var.app_name}/${var.workspace_name}/${var.table_logical_name}/arn"
  value = aws_dynamodb_table.t.arn
}

resource "aws_ssm_parameter" "stream_arn" {
  type        = "String"
  description = "ARN of DynamoDB Layers Table Stream"
  name        = "/${var.app_name}/${var.workspace_name}/${var.table_logical_name}/stream/arn"
  value       = aws_dynamodb_table.t.stream_arn
}

resource "aws_ssm_parameter" "stream_label" {
  type        = "String"
  description = "Lable of DynamoDB Stream"
  name        = "/${var.app_name}/${var.workspace_name}/${var.table_logical_name}/stream/label"
  value       = aws_dynamodb_table.t.stream_label
}
