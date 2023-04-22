data "aws_iam_policy_document" "github_role_push_to_ecr" {
  statement {
    ## https://github.com/aws-actions/amazon-ecr-login
    actions = [
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:GetDownloadUrlForLayer",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart",
        "ecr:DescribeImages"
      ]
    resources = ["arn:aws:ecr:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"]  # all ecr repositories
  }

  statement {
    actions = ["ecr:GetAuthorizationToken"]
    resources = ["*"]  # Needed for logging in
  }

  statement {
    actions = ["ssm:PutParameter"]
    resources = ["arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.app_name}/*"]  # Needed for logging in
  }
}

resource "aws_iam_policy" "ecr_policy_for_github" {
  name        = "github_push_to_ecr"
  path        = "/"
  description = "Policy for Github role to push to ECR"
  policy = data.aws_iam_policy_document.github_role_push_to_ecr.json
}

resource "aws_iam_role_policy_attachment" "attach_on_push" {
  role       = aws_iam_role.github_role.name
  policy_arn = aws_iam_policy.ecr_policy_for_github.arn
}