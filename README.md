# CAB432 A2 Video Transcoder (Stateless)

- FastAPI backend (Cognito JWT, S3 presigned URLs, DynamoDB job metadata)
- Stateless: all data in S3/DynamoDB; instance can be replaced anytime

## Quick start

```bash
cp .env.example .env  # edit if needed

docker build -t video-transcoder:latest .
docker rm -f video-transcoder 2>/dev/null

# pick ONE of these (depending on the port you opened)
docker run -d --name video-transcoder --restart=unless-stopped   --env-file .env -p 80:8080 video-transcoder:latest
# or:
# docker run -d --name video-transcoder --restart=unless-stopped #   --env-file .env -p 8080:8080 video-transcoder:latest
```

Open Swagger: `http://<EC2_PUBLIC_DNS>/docs` (or `:8080/docs`)
Authorize with your **Cognito ID token** (`Bearer <token>`).
