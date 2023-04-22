data "aws_iam_policy_document" "github_role_on_push" {
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${var.config_bucket_arn}/*"]
  }

  statement {
    actions = ["ssm:GetParameter"]
    resources = ["arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.app_name}/*"]
  }

  statement {
    actions = ["ssm:GetParameter"]
    resources = ["arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/gh*"]  # all github stacks
  }

  statement {
    actions = ["states:StartExecution"]
    resources = ["arn:aws:states:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stateMachine:gh-*"]  # all github statemachines
  }

}

resource "aws_iam_policy" "github_role_on_push" {
  name        = "github_on_push"
  path        = "/"
  description = "Policy for Github role on push"
  policy = data.aws_iam_policy_document.github_role_on_push.json
}

resource "aws_iam_role_policy_attachment" "attach_github_on_push" {
  role       = aws_iam_role.github_role.name
  policy_arn = aws_iam_policy.github_role_on_push.arn
}