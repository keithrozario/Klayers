resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "https://github.com/${var.github_org}",
  ]
  
  ## https://github.blog/changelog/2022-01-13-github-actions-update-on-oidc-based-deployments-to-aws/
  ## https://awsteele.com/blog/2021/09/15/aws-federation-comes-to-github-actions.html
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1"
    ]
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "github_actions_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo_name}:*"]
    }
  }
}

data "aws_iam_policy_document" "github_role_inline_policy" {
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${var.config_bucket_arn}/*"]
  }

  statement {
    actions = ["ssm:GetParameter"]
    resources = ["arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.app_name}/*"]
  }
}

resource "aws_iam_role" "github_role" {
  name = var.github_role_name
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role_policy.json
  inline_policy {
    name   = "klayers-inline-policy"
    policy = data.aws_iam_policy_document.github_role_inline_policy.json
  }
}

