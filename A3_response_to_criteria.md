## Project Core - Microservices

- **First service functionality:** : Handles CPU-intensive video processing and transcoding tasks (the main compute-heavy service that scales horizontally based on load).
- **First service compute:** 11874104_video-processing-task-service-443wsd76
- **First service source files:: app.py, Dockerfile, requirements.txt
  - 

- **Second service functionality:: Api calling 
- **Second service compute:n10886524-task-defination-service-7rws2dsv
- **Second service source files:app.py, Dockerfile, requirements.txt
  - 

- **Video timestamp:**


## Project Additional - Additional microservices

- **Third service functionality:Heath check 
- **Third service compute:n10886524-task-defination-service-fegsy8xp
- **Third service source files:app.py, Dockerfile, requirements.txt
  - 

- **Fourth service functionality:fault taularence
- **Fourth service compute:n10886524-task-defination-service-uh7ipdv5


- **Fourth service source files:app.py, Dockerfile, requirements.txt
  - 

- **Video timestamp:**


## Project Additional - Serverless functions

- **Service(s) deployed on Lambda:video-jobs-dlq-handler-n10886524
- **Video timestamp:**
- **Relevant files:lambda_functions
    -


## Project Additional - Container orchestration with ECS 

- **ECS cluster name:video-processing-cluster-n10886524
- **Task definition names:events-service-task-n10886524:2/ worker-task-n10886524:1
- **Video timestamp:**
- **Relevant files:task1.py
    -


## Project Core - Load distribution

- **Load distribution mechanism:** [eg. SQS, ALB,...]
- **Mechanism instance name:** [eg. n1234567-project-alb]
- **Video timestamp:**
- **Relevant files:**
    -


## Project Additional - Communication mechanisms

- **Communication mechanism(s):SQS, EventBridge, Ecs, Eventservice
- **Mechanism instance name:video-jobs-n10886524
- **Video timestamp:**
- **Relevant files:aws deployment
    -


## Project Core - Autoscaling

- **EC2 Auto-scale group or ECS Service name:n10886524_cpu_service_asg
- **Video timestamp:**
- **Relevant files:aws deployment
    -


## Project Additional - Custom scaling metric

- **Description of metric:awsec2-i-01f2501f24e105a4a-GreaterThanOrEqualToThreshold-CPUUtilization
- **Implementation:** [eg. custom cloudwatch metric with lambda]
- **Rationale:: n10886524-simple-scaling, n10886524-target-tracking-policy
- **Video timestamp:**
- **Relevant files:aws deployment
    -


## Project Core - HTTPS

- **Domain name:n10886524.cab432.com
- **Certificate ID:**
- **ALB/API Gateway name:n10886524-cpu-service-alb
- **Video timestamp:**
- **Relevant files:aws deployment
    -


## Project Additional - Container orchestration features

- **First additional ECS feature:** [eg. service discovery]
- **Second additional ECS feature:**
- **Video timestamp:**
- **Relevant files:**
    -


## Project Additional - Infrastructure as Code

- **Technology used:Terraform
- **Services deployed:LB, SQS, lamda , laumch template, IAM .
- **Video timestamp:**
- **Relevant files:terraform
    -


## Project Additional - Dead letter queue

- **Technology used:SQS, Lamda  
- **Services deployed: video-jobs-dlq-n10886524
- **Video timestamp:**
- **Relevant files:aws deployment
    -


## Project Additional - Edge Caching

- **Cloudfront Distribution ID:EDDN4R9VO91IP
- **Content cached:: index1.html file stored in the S3 bucket assignment-cacheing-n10886524
- **Rationale for caching:The index1.html page is served via CloudFront to reduce latency and improve load times for repeated accesses. By setting the cache control header "max-age=60, must-revalidate", CloudFront stores this static HTML page temporarily at edge locations. This ensures that frequent requests are served locally while still refreshing the cache every 60 seconds for updated content.
- **Video timestamp:**
- **Relevant files:index1.html
    -


## Project Additional - Other (with prior permission only)

- **Description:**
- **Video timestamp:**
- **Relevant files:**
    -
