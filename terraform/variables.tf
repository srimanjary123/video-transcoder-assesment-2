variable "aws_region" { default = "ap-southeast-2" }
variable "vpc_cidr" { default = "10.0.0.0/16" }
variable "public_subnets" { default = ["10.0.1.0/24", "10.0.2.0/24"] }
variable "instance_type" { default = "t3.micro" } # change per budget
variable "desired_capacity" { default = 1 }
variable "min_size" { default = 1 }
variable "max_size" { default = 3 }
variable "key_name" { default = "" } # optional EC2 key pair
