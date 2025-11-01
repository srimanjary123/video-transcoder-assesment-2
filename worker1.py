#!/usr/bin/env python3
"""
SQS worker for CPU-intensive video transcode jobs.

Expects env:
  - AWS_REGION=ap-southeast-2
  - SQS_QUEUE_URL=<your SQS queue url>
Requires:
  - ffmpeg installed on the machine
  - Instance role or creds with sqs:Receive/Delete/Get*, s3:Get/Put/List
"""

import os
import json
import uuid
import subprocess
import traceback
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
QUEUE_URL = os.environ.get("SQS_QUEUE_URL")

if not QUEUE_URL:
    raise RuntimeError("SQS_QUEUE_URL is not set")

sqs = boto3.client("sqs", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

def run_ffmpeg(src_path: str, dst_path: str) -> None:
    """
    Transcode using ffmpeg. Tweak flags to match your rubric if needed.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", src_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        dst_path,
    ]
    print(f"[FFMPEG] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def process_message(msg: dict) -> None:
    """
    Message body format:
      {
        "job_id": "...",
        "input_bucket": "...",
        "input_key": "inputs/sample.mp4",
        "output_bucket": "...",
        "output_prefix": "outputs/",
        "target_format": "mp4"
      }
    """
    body = json.loads(msg["Body"])

    job_id = body.get("job_id") or str(uuid.uuid4())
    in_bkt = body["input_bucket"]
    in_key = body["input_key"]
    out_bkt = body["output_bucket"]
    out_prefix = body.get("output_prefix", "outputs/")
    out_fmt = body.get("target_format", "mp4")

    # local temp paths
    local_in = f"/tmp/in-{job_id}"
    local_out = f"/tmp/out-{job_id}.{out_fmt}"

    print(f"[{job_id}] Download s3://{in_bkt}/{in_key} -> {local_in}")
    s3.download_file(in_bkt, in_key, local_in)

    print(f"[{job_id}] Transcoding -> {local_out}")
    run_ffmpeg(local_in, local_out)

    out_key = f"{out_prefix}{os.path.basename(local_out)}"
    print(f"[{job_id}] Upload {local_out} -> s3://{out_bkt}/{out_key}")
    s3.upload_file(local_out, out_bkt, out_key)

    # best effort cleanup
    try:
        os.remove(local_in)
        os.remove(local_out)
    except OSError:
        pass

    print(f"[{job_id}] DONE -> s3://{out_bkt}/{out_key}")

def main() -> None:
    print(f"[BOOT] Worker starting in region={REGION}")
    print(f"[BOOT] Queue={QUEUE_URL}")

    while True:
        try:
            resp = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,    # long poll
                VisibilityTimeout=600  # keep >= worst-case ffmpeg time
            )
        except (EndpointConnectionError, ClientError) as e:
            print(f"[SQS ERR] {e}")
            continue

        messages = resp.get("Messages", [])
        if not messages:
            continue

        for m in messages:
            receipt = m["ReceiptHandle"]
            try:
                process_message(m)
                # delete only on success
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt)
            except subprocess.CalledProcessError as e:
                print(f"[FFMPEG ERROR] returncode={e.returncode}")
                print(getattr(e, 'stderr', ''))
                print(traceback.format_exc())
                # do NOT delete -> message will be retried or sent to DLQ
            except (ClientError, NoCredentialsError) as e:
                print(f"[AWS ERROR] {e}")
            except Exception as e:
                print(f"[UNKNOWN ERROR] {e}")
                print(traceback.format_exc())

if __name__ == "__main__":
    main()

