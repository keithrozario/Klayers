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

## Role

data "aws_iam_policy_document" "github_actions_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type = "Federated"
      identifiers = [module.oidc_github.github_oidc_provider_arn]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.website_github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "website_github_role" {
  name = var.website_role_name
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role_policy.json
}

data "aws_iam_policy_document" "website_github_role" {
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.website_bucket.arn}/*"]
  }
}

resource "aws_iam_policy" "website_github_policy" {
  name        = "github-action-website"
  path        = "/"
  description = "Sync to website bucket"
  policy = data.aws_iam_policy_document.website_github_role.json
}

resource "aws_iam_role_policy_attachment" "attach_github_on_push" {
  role       = aws_iam_role.website_github_role.name
  policy_arn = aws_iam_policy.website_github_policy.arn
}