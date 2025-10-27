# lambda_iam.tf — add this to your terraform folder

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "lambda-publish-metric-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

# Inline policy for Lambda to read ALB metrics, describe targets, and put custom metrics
data "aws_iam_policy_document" "lambda_policy" {
  statement {
    effect = "Allow"

    actions = [
      "cloudwatch:GetMetricStatistics",
      "cloudwatch:PutMetricData",
      "cloudwatch:ListMetrics",
      "elasticloadbalancing:DescribeTargetHealth",
      "elasticloadbalancing:DescribeTargetGroups",
      "ec2:DescribeInstances"
    ]

    resources = ["*"]
  }

  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy" "lambda_inline_policy" {
  name   = "lambda-publish-metric-inline"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_policy.json
}
