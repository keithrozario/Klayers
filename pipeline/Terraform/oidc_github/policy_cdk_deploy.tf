data "aws_iam_policy_document" "github_role_cdk_deploy" {
  statement {
    actions = [
      "sts:AssumeRole",
      "sts:TagSession"
    ]
    resources = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/cdk-hnb659fds-*"]
  }

  statement {
    actions = [
      "cloudformation:DescribeStacks",
      "lambda:ListFunctions"
    ]
    resources = ["*"]
  }

  statement {
    actions   = ["s3:ListBucket"]
    resources = [var.config_bucket_arn]
  }

  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.app_name}/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/common-service/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/cdk-bootstrap/*"
    ]
  }

  statement {
    actions   = ["events:PutEvents"]
    resources = ["arn:aws:events:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:event-bus/default"]
  }

  statement {
    actions = ["lambda:InvokeFunction"]
    resources = [
      "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:klayers-*",
      "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:kl-*"
    ]
  }
}

resource "aws_iam_policy" "cdk_deploy_for_github" {
  name        = "github_cdk_deploy"
  path        = "/"
  description = "Policy for Github role to deploy CDK stacks and invoke pipeline operations"
  policy      = data.aws_iam_policy_document.github_role_cdk_deploy.json
}

resource "aws_iam_role_policy_attachment" "attach_cdk_deploy" {
  role       = aws_iam_role.github_role.name
  policy_arn = aws_iam_policy.cdk_deploy_for_github.arn
}
