variable "s3bucket_layers" { type = map(any) }

## S3 Bucket
resource "aws_s3_bucket" "s3bucket_layers" {
  bucket        = lookup(var.s3bucket_layers, local.workspace_full_name)
  force_destroy = true
}


resource "aws_s3_bucket_public_access_block" "layers_bucket" {
  bucket = aws_s3_bucket.s3bucket_layers.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "s3bucket_layers_versioning" {
  bucket = aws_s3_bucket.s3bucket_layers.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "s3bucket_layers_bucket_config" {
  # Must have bucket versioning enabled first
  depends_on = [aws_s3_bucket_versioning.s3bucket_layers_versioning]
  bucket     = aws_s3_bucket.s3bucket_layers.id
  rule {
    id = "layers-lifecycle"
    noncurrent_version_transition {
      noncurrent_days = 7
      storage_class   = "DEEP_ARCHIVE"
    }
    status = "Enabled"
  }
}

resource "aws_ssm_parameter" "layers_bucket_name" {
  type        = "String"
  description = "Name of s3 bucket to hold layer artifacts"
  name        = "/${var.app_name}/${local.workspace_full_name}/layers_bucket/name"
  value       = aws_s3_bucket.s3bucket_layers.bucket
  overwrite   = true
}

resource "aws_ssm_parameter" "layers_bucket_arn" {
  type        = "String"
  description = "ARN of layer bucket"
  name        = "/${var.app_name}/${local.workspace_full_name}/layers_bucket/arn"
  value       = aws_s3_bucket.s3bucket_layers.arn
  overwrite   = true
}

## Config Bucket -- to be uploaded from github

resource "aws_s3_bucket" "s3bucket_config" {
  bucket_prefix = "klayers-config-${var.app_name}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "config_bucket" {
  bucket = aws_s3_bucket.s3bucket_config.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_ssm_parameter" "config_bucket_name" {
  type        = "String"
  description = "Name of s3 bucket to hold configuration files"
  name        = "/${var.app_name}/${local.workspace_full_name}/config_bucket/name"
  value       = aws_s3_bucket.s3bucket_config.bucket
  overwrite   = true
}

resource "aws_ssm_parameter" "config_bucket_arn" {
  type        = "String"
  description = "ARN of config bucket"
  name        = "/${var.app_name}/${local.workspace_full_name}/config_bucket/arn"
  value       = aws_s3_bucket.s3bucket_config.arn
  overwrite   = true
}


## DynamoDB backup bucket config
resource "aws_s3_bucket" "s3bucket_ddb_backup" {
  bucket_prefix = "ddb-backup"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "ddb_backup" {
  bucket = aws_s3_bucket.s3bucket_ddb_backup.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "ddb_backup_versioning" {
  bucket = aws_s3_bucket.s3bucket_ddb_backup.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "ddb_backup_bucket_config" {
  # Must have bucket versioning enabled first
  depends_on = [aws_s3_bucket_versioning.ddb_backup_versioning]
  bucket     = aws_s3_bucket.s3bucket_ddb_backup.id
  rule {
    id = "backup-lifecycle"
    noncurrent_version_transition {
      noncurrent_days = 5
      storage_class   = "DEEP_ARCHIVE"
    }
    status = "Enabled"
  }
}


# Website bucket

resource "aws_s3_bucket" "website_bucket" {
  force_destroy = true
}

resource "aws_ssm_parameter" "website_bucket_name" {
  type        = "String"
  description = "Name of s3 bucket to hold website"
  name        = "/${var.app_name}/${local.workspace_full_name}/website_bucket/name"
  value       = aws_s3_bucket.website_bucket.bucket
}

resource "aws_s3_bucket_public_access_block" "website_bucket" {
  bucket = aws_s3_bucket.website_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}