# ec2_iam.tf — add this to your terraform folder

# Policy document for EC2 assume role
data "aws_iam_policy_document" "ec2_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# EC2 Role
resource "aws_iam_role" "ec2_role" {
  name               = "ec2-role-push-metrics"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

# Minimal inline policy document to allow push to CloudWatch
data "aws_iam_policy_document" "ec2_policy" {
  statement {
    effect = "Allow"

    actions = [
      "cloudwatch:PutMetricData"
    ]

    resources = ["*"]
  }
}

# Attach the inline policy to the role
resource "aws_iam_role_policy" "ec2_role_inline" {
  name   = "ec2-put-metric-policy"
  role   = aws_iam_role.ec2_role.id
  policy = data.aws_iam_policy_document.ec2_policy.json
}

# Instance Profile used by the launch template (name must match launch_template.tf)
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ec2-instance-profile"
  role = aws_iam_role.ec2_role.name
}
