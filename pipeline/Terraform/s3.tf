variable "s3bucket_layers" { type = map(any) }

## S3 Bucket
resource "aws_s3_bucket" "s3bucket_layers" {
  bucket        = lookup(var.s3bucket_layers, local.workspace_full_name)
  force_destroy = true
}

resource "aws_s3_bucket_acl" "s3bucket_layers_acl" {
  bucket = aws_s3_bucket.s3bucket_layers.id
  acl    = "private"
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
  bucket = aws_s3_bucket.s3bucket_layers.id
  rule {
    id = "layers-lifecycle"
    noncurrent_version_transition {
      noncurrent_days = 2
      storage_class   = "DEEP_ARCHIVE"
    }
    status = "Enabled"
  }
}

resource "aws_ssm_parameter" "layers_bucket_name" {
  type        = "String"
  description = "Name of s3 bucket to hold layer artifacts"
  name        = "/${lookup(var.app_name, local.workspace_full_name)}/${local.workspace_full_name}/layers_bucket/name"
  value       = aws_s3_bucket.s3bucket_layers.bucket
  overwrite   = true
}

resource "aws_ssm_parameter" "layers_bucket_arn" {
  type        = "String"
  description = "ARN of layer bucket"
  name        = "/${lookup(var.app_name, local.workspace_full_name)}/${local.workspace_full_name}/layers_bucket/arn"
  value       = aws_s3_bucket.s3bucket_layers.arn
  overwrite   = true
}

## Configuration Files
resource "aws_s3_bucket_object" "packages_config" {
  bucket = aws_s3_bucket.s3bucket_layers.bucket
  key    = "config/packages.csv"
  source = "../config/${local.workspace_full_name}/packages.csv"
}

resource "aws_s3_bucket_object" "regions_config" {
  bucket = aws_s3_bucket.s3bucket_layers.bucket
  key    = "config/regions.csv"
  source = "../config/${local.workspace_full_name}/regions.csv"
}