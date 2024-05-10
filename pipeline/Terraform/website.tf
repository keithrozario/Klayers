# Creates the bucket and CDN for the website.data
resource "aws_s3_bucket" "website_bucket" {
  provider = aws.cloudfront

  bucket_prefix = "klayers-website"
  force_destroy = true
}

resource "aws_ssm_parameter" "website_bucket_name" {
  provider = aws.cloudfront
  type        = "String"
  description = "Name of s3 bucket to hold website"
  name        = "/${var.app_name}/${local.workspace_full_name}/website_bucket/name"
  value       = aws_s3_bucket.website_bucket.bucket
}

resource "aws_s3_bucket_public_access_block" "website_bucket" {
  provider = aws.cloudfront
  bucket = aws_s3_bucket.website_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

module "cdn" {
  providers = {
    aws = aws.cloudfront
  }
  source = "cloudposse/cloudfront-s3-cdn/aws"
  version = "0.94.0"

  origin_bucket     = aws_s3_bucket.website_bucket.id
  aliases           = [lookup(var.website_domain_name, local.workspace_full_name)]
  acm_certificate_arn = module.website_certificate.cert_arn
  depends_on = [module.website_certificate]
  cloudfront_access_logging_enabled = false
  name = lookup(var.website_domain_name, local.workspace_full_name)
}


## This has to be manually set in Cloudflare.
module "website_certificate" {
  source          = "./certificate_manager"
  api_domain_name = lookup(var.website_domain_name, local.workspace_full_name)
  app_name        = var.app_name
  workspace_name  = local.workspace_full_name

  providers = {
    aws = aws.cloudfront
  }

}