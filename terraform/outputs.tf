# outputs.tf

# ALB DNS name output
output "alb_dns" {
  description = "Application Load Balancer DNS name"
  value       = aws_lb.app.dns_name
}

# Target Group ARN
output "target_group_arn" {
  description = "Target group ARN"
  value       = aws_lb_target_group.app_tg.arn
}

# Auto Scaling Group name
output "asg_name" {
  description = "Auto Scaling Group name"
  value       = aws_autoscaling_group.app_asg.name
}
