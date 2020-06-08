variable "s3bucket_layers" { type = map }

## S3 Bucket
resource "aws_s3_bucket" "s3bucket_layers" {
  bucket        = lookup(var.s3bucket_layers, terraform.workspace)
  acl           = "private"
  force_destroy = true
  region        = lookup(var.aws_region, terraform.workspace)

  versioning {
    enabled = true
  }

  lifecycle_rule {

    enabled = true

    noncurrent_version_transition {
      days          = 7
      storage_class = "DEEP_ARCHIVE"
    }
  }

}

resource "aws_ssm_parameter" "layers_bucket_name" {
  type        = "String"
  description = "Name of s3 bucket to hold layer artifacts"
  name        = "/${lookup(var.app_name, terraform.workspace)}/${terraform.workspace}/layers_bucket/name"
  value       = aws_s3_bucket.s3bucket_layers.bucket
  overwrite   = true
}

resource "aws_ssm_parameter" "layers_bucket_arn" {
  type        = "String"
  description = "ARN of layer bucket"
  name        = "/${lookup(var.app_name, terraform.workspace)}/${terraform.workspace}/layers_bucket/arn"
  value       = aws_s3_bucket.s3bucket_layers.arn
  overwrite   = true
}

## Configuration Files
resource "aws_s3_bucket_object" "packages_config" {
  bucket = aws_s3_bucket.s3bucket_layers.bucket
  key    = "config/packages.csv"
  source = "../config/${terraform.workspace}/packages.csv"
}

resource "aws_s3_bucket_object" "regions_config" {
  bucket = aws_s3_bucket.s3bucket_layers.bucket
  key    = "config/regions.csv"
  source = "../config/${terraform.workspace}/regions.csv"
}