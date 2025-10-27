#!/bin/bash
yum update -y
yum install -y httpd python3
cat <<'EOF' >/var/www/html/index.html
<html><body><h1>Hello from Terraform ASG instance</h1></body></html>
EOF
systemctl enable httpd
systemctl start httpd
# Optionally start a background script that pushes metrics using instance metadata (if you want)
