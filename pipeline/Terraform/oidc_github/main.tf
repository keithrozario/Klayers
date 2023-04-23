data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "https://github.com/${var.github_org}", # github script
    "sts.amazonaws.com" # aws-actions/configure-aws-credentials@v1
  ]
  
  ## https://github.blog/changelog/2022-01-13-github-actions-update-on-oidc-based-deployments-to-aws/
  ## https://awsteele.com/blog/2021/09/15/aws-federation-comes-to-github-actions.html
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1"
    ]
}

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

resource "aws_iam_role" "github_role" {
  name = var.github_role_name
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role_policy.json
}


