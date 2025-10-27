resource "aws_autoscaling_group" "app_asg" {
  name             = "app-asg"
  max_size         = var.max_size
  min_size         = var.min_size
  desired_capacity = var.desired_capacity
  launch_template {
    id      = aws_launch_template.app_lt.id
    version = "$Latest"
  }
  vpc_zone_identifier       = [for s in aws_subnet.public : s.id]
  target_group_arns         = [aws_lb_target_group.app_tg.arn]
  health_check_type         = "ELB"
  health_check_grace_period = 60
  tag {
    key                 = "Name"
    value               = "app-asg-instance"
    propagate_at_launch = true
  }
}

# Target tracking scaling policy using ALBRequestCountPerTarget
resource "aws_autoscaling_policy" "alb_target_tracking" {
  name                   = "alb-rps-target"
  autoscaling_group_name = aws_autoscaling_group.app_asg.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      # resource_label optional: "<loadbalancer-arn>/<targetgroup-arn>"
      resource_label = "${aws_lb.app.arn_suffix}/${aws_lb_target_group.app_tg.arn_suffix}"
    }
    target_value = 10.0 # requests per target (tweak for your load)
  }
}
