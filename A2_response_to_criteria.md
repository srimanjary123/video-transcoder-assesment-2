Assignment 2 - Cloud Services Exercises - Response to Criteria
================================================

Instructions
------------------------------------------------
- Keep this file named A2_response_to_criteria.md, do not change the name
- Upload this file along with your code in the root directory of your project
- Upload this file in the current Markdown format (.md extension)
- Do not delete or rearrange sections.  If you did not attempt a criterion, leave it blank
- Text inside [ ] like [eg. S3 ] are examples and should be removed


Overview
------------------------------------------------

- **Name:** Shivanshi Patel
- **Student number:** n11632968
- **Partner name (if applicable):Srimanjary Paul
- **Student number:** n10886524
- **Application name:** CAB432 A2 Video Transcoder (Stateless)
- **Two line description:** FastAPI video transcoder running in Docker on EC2. Files are stored in S3, job state in DynamoDB; additional demos include RDS, ElastiCache, Parameter Store, Secrets Manager, Cognito, and Route53.
- **EC2 instance name or ID:** i-0f39cdc6cf9de3198

------------------------------------------------

### Core - First data persistence service

- **AWS service name:**  Amazon S3
- **What data is being stored?:** Uploaded source videos and transcoded outputs
- **Why is this service suited to this data?:** Durable object storage with presigned URL access suited to large binary files
- **Why is are the other services used not suitable for this data?:** DynamoDB/RDS are not intended for large blobs; EBS is tied to a single instance
- **Bucket/instance/table name:** n10886524-assessment2
- **Video timestamp:**
- 00:25
- **Relevant files:**
    - app.py
    - Dockerfile
    - requirements.txt

### Core - Second data persistence service

- **AWS service name:**  Amazon DynamoDB
- **What data is being stored?:** Job records (job_id, input/output S3 keys, status, timestamps)
- **Why is this service suited to this data?:** They store JSON-like items and fetch them quickly by an ID, without managing any servers. As traffic grows, the service automatically scales to handle more requests while keeping responses fast.
- **Why is are the other services used not suitable for this data?:** S3 lacks query semantics; RDS adds schema/ops for simple status reads
- **Bucket/instance/table name:** n10886524-jobs
- **Video timestamp:**
- 01:10
- **Relevant files:**
    - app.py

### Third data service

- **AWS service name:**  Amazon RDS (PostgreSQL)
- **What data is being stored?:** Demo table jobs_demo(id, status, created_at) in schema s307
- **Why is this service suited to this data?:** SQL features and constraints for relational access
- **Why is are the other services used not suitable for this data?:** Complex queries are inefficient in DynamoDB and not available in S3
- **Bucket/instance/table name:** Endpoint database-1-instance-1.ce2haupt2cta.ap-southeast-2.rds.amazonaws.com, DB cohort_2025, Schema s307, Table jobs_demo
- **Video timestamp:**
- 01:55 
- **Relevant files:**
    - rds_demo.py

### S3 Pre-signed URLs

- **S3 Bucket names:** n10886524-assessment2
- **Video timestamp:**
- 02:40 
- **Relevant files:**
    - app.py

### In-memory cache

- **ElastiCache instance name:** n11632968-mc.km2jzi.cfg.apse2.cache.amazonaws.com:11211
- **What data is being cached?:** Repeated HTTP fetch used in the demo to show cache miss then hits
- **Why is this data likely to be accessed frequently?:** The same resource is requested multiple times during normal use
- **Video timestamp:**
- 03:20 
- **Relevant files:**
    - memcached.py

### Core - Statelessness

- **What data is stored within your application that is not stored in cloud data services?:** Temporary working files during a transcode and in-memory request state
- **Why is this data not considered persistent state?:** It can be recreated from S3 sources if lost
- **How does your application ensure data consistency if the app suddenly stops?:** Job status is persisted in DynamoDB and outputs are written to S3 before final status update
- **Relevant files:**
    - app.py

### Graceful handling of persistent connections

- **Type of persistent connection and use:** Client polling of job status endpoint
- **Method for handling lost connections:** Client retries with backoff; server reads authoritative state from DynamoDB
- **Relevant files:**
    - app.py


### Core - Authentication with Cognito

- **User pool name:** n10886524 - userpool
- **How are authentication tokens handled by the client?:** Bearer tokens from hosted UI login sent with API requests
- **Video timestamp:**
- 04:30
- **Relevant files:**
    - app.py
    

### Cognito multi-factor authentication

- **What factors are used for authentication:** Password + TOTP (Authenticator app) with Optional MFA
- **Video timestamp:**
- **Relevant files:**
    - index.html

### Cognito federated identities

- **Identity providers used:**
- **Video timestamp:**
- **Relevant files:**
    - 

### Cognito groups - attempted in code

- **How are groups used to set permissions?:**
- **Video timestamp:**
- **Relevant files:**
    - 

### Core - DNS with Route53

- **Subdomain**:  n11632968.cab432.com
- **Video timestamp:**
- 05:40

### Parameter store

- **Parameter names:** /cab432/n11632968/a2/api_base_url, /cab432/n11632968/a2/presets, /cab432/n11632968/a2/s3_bucket
- **Video timestamp:**
- **Relevant files:**
    - app.py

### Secrets manager

- **Secrets names:** n11632968-demosecret
- **Video timestamp:**
- **Relevant files:**
    - aws_secrets.py

### Infrastructure as code

- **Technology used:** Dockerfile and scripted AWS CLI steps
- **Services deployed:** FastAPI container on EC2 integrating S3, DynamoDB, ElastiCache, RDS demo
- **Video timestamp:**
- **Relevant files:**
    - Dockerfile
    - requirements.txt

### Other (with prior approval only)

- **Description:**
- **Video timestamp:**
- **Relevant files:**
    - 

### Other (with prior permission only)

- **Description:**
- **Video timestamp:**
- **Relevant files:**
    - 
