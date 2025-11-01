import boto3
import json
import time
import logging
import os
# AWS setup
region = "ap-southeast-2"
sqs = boto3.client('sqs', region_name=region)
events = boto3.client('events', region_name=region)

# Environment variables from ECS task
QUEUE_URL = os.environ.get("https://sqs.ap-southeast-2.amazonaws.com/901444280953/video-jobs-n10886524")
EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME", "default")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

def process_job(job):
    """Simulate video processing work"""
    logger.info(f"Processing job {job['jobId']} for user {job['user']}")
    time.sleep(3)  # simulate processing delay
    return {"status": "COMPLETED", "output": f"s3://video-output/{job['jobId']}.mp4"}

def send_event(job_id, status, output_url):
    """Publish VideoJob.StateChanged event to EventBridge"""
    event_detail = {
        "jobId": job_id,
        "status": status,
        "output": output_url
    }

    response = events.put_events(
        Entries=[{
            "Source": "my.video.worker",
            "DetailType": "VideoJob.StateChanged",
            "Detail": json.dumps(event_detail),
            "EventBusName": EVENT_BUS_NAME
        }]
    )

    logger.info(f"Event sent to EventBridge: {json.dumps(event_detail)}")
    return response

def poll_queue():
    """Poll SQS queue and process messages"""
    logger.info("Worker started. Polling for messages...")

    while True:
        resp = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )

        messages = resp.get("Messages", [])
        if not messages:
            continue

        for msg in messages:
            body = json.loads(msg["Body"])
            job = body if isinstance(body, dict) else json.loads(body)

            try:
                result = process_job(job)
                send_event(job["jobId"], result["status"], result["output"])
            except Exception as e:
                logger.exception(f"Error processing job {job}: {e}")

            # delete message from queue
            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=msg["ReceiptHandle"]
            )
            logger.info(f"Job {job['jobId']} processed and deleted.")

if __name__ == "__main__":
    poll_queue()

#Dockerfile
FROM python:3.11-slim
WORKDIR /app
# Copy files and install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]



  
