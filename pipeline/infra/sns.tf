resource "aws_sns_topic" "lambda_error_notification" {
  name_prefix = "lambda_notification"

  delivery_policy = <<EOF
{
  "http": {
    "defaultHealthyRetryPolicy": {
      "minDelayTarget": 10,
      "maxDelayTarget": 180,
      "numRetries": 5,
      "numMaxDelayRetries": 2,
      "numNoDelayRetries": 0,
      "numMinDelayRetries": 2,
      "backoffFunction": "linear"
    },
    "disableSubscriptionOverrides": false,
    "defaultThrottlePolicy": {
      "maxReceivesPerSecond": 1
    }
  }
}
EOF
}

resource "aws_ssm_parameter" "lambda_error_notification_arn" {
  type  = "String"
  description = "ARN of SNS Topic for Lambda Notification"
  name  = "/${lookup(var.app_name, terraform.workspace)}/${terraform.workspace}/lambda_error_notification_arn"
  value = "${aws_sns_topic.lambda_error_notification.arn}"
  overwrite = true
}
