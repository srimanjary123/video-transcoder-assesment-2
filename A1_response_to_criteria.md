Assignment 1 - REST API Project - Response to Criteria
================================================

Overview
------------------------------------------------

- **Name:** Your Name
- **Student number:** 
- **Application name:** VideoTranscoderAPI
- **Two line description:**  
  This REST API, built with Python FastAPI, allows authenticated users to upload videos which are transcoded into multiple formats using `ffmpeg`.  
  The application also manages video metadata, supports multiple data types, and is deployed to AWS using Docker and EC2.

Core criteria
------------------------------------------------

### Containerise the app

- **ECR Repository name:** `video-transcoder`
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `Dockerfile`
  - `requirements.txt`

### Deploy the container

- **EC2 instance ID:** [Insert instance ID]  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `deploy.sh` (if used)
  - `docker-compose.yml` (if used)

### User login

- **One line description:** JWT-based authentication implemented with FastAPI’s security utilities (`OAuth2PasswordBearer`) and `python-jose`.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `app/auth.py`
  - `app/models.py`
  - `app/main.py`

### REST API

- **One line description:** Endpoints built with FastAPI to upload videos, fetch metadata, check transcoding status, and download results.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `app/main.py`
  - `app/routers/videos.py`
  - `app/schemas.py`

### Data types

- **One line description:** API handles binary video uploads and JSON metadata.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `app/schemas.py`
  - `app/main.py`

#### First kind

- **One line description:** Video file upload → transcoded with `ffmpeg`.  
- **Type:** Binary (MP4, AVI, MKV).  
- **Rationale:** Demonstrates CPU-intensive processing, realistic use case.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `app/transcoder.py`

#### Second kind

- **One line description:** JSON metadata for video file (name, format, duration, status).  
- **Type:** JSON.  
- **Rationale:** Structured format supports API queries and persistent storage.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `app/schemas.py`
  - `app/models.py`

### CPU intensive task

- **One line description:** Transcoding implemented with Python subprocess calls to `ffmpeg`, converting uploaded videos to multiple formats.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `app/transcoder.py`

### CPU load testing

- **One line description:** Load testing performed using Apache Bench (`ab`) and Locust to simulate concurrent uploads and monitor CPU load.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `tests/load_test.sh`
  - `README.md` (load testing notes)

Additional criteria
------------------------------------------------

### Extensive REST API features

- **One line description:** Implemented pagination (`skip/limit` query params) and filtering for video metadata endpoints. Added versioned routes (`/api/v1/`).  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `app/routers/videos.py`

### External API(s)

- **One line description:** Integrated AWS Rekognition API to generate labels/thumbnails for uploaded videos.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `app/external_api.py`

### Additional types of data

- **One line description:** API also accepts image files (JPEG/PNG) to store and link thumbnails.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `app/routers/images.py`
  - `app/schemas.py`

### Custom processing

- **One line description:** Automatic thumbnail generation from first frame of video using `ffmpeg` inside FastAPI background task.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `app/transcoder.py`

### Infrastructure as code

- **One line description:** Provisioned AWS EC2 instance and ECR repo using Terraform (IaC).  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `infra/main.tf`
  - `infra/variables.tf`

### Web client

- **One line description:** Simple HTML/JavaScript client served alongside FastAPI to upload videos and poll transcoding status.  
- **Video timestamp:** [Insert timestamp]  
- **Relevant files:**
  - `client/index.html`
  - `client/script.js`

### Upon request

- **One line description:** 
- **Video timestamp:**  
- **Relevant files:**
