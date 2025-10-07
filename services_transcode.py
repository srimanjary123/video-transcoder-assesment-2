import os
import time
import subprocess
from botocore.exceptions import ClientError
from db_videos import update
from storage_s3 import download_file, upload_file

def _run(cmd: list) -> tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout

def transcode_task(job_id: str, input_key: str, preset: str = "480p"):
    """
    Download from S3 -> FFmpeg transcode -> upload to S3 -> update DynamoDB.
    """
    try:
        update(job_id, status="processing", started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

        base = f"/tmp/{job_id}"
        os.makedirs(base, exist_ok=True)
        in_path = f"{base}/input"
        out_path = f"{base}/output.mp4"

        download_file(input_key, in_path)

        vf = {"360p": "scale=-2:360", "480p": "scale=-2:480", "720p": "scale=-2:720"}.get(preset, "scale=-2:480")
        rc, logs = _run([
            "ffmpeg", "-y", "-i", in_path, "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-c:a", "aac", out_path
        ])
        if rc != 0 or not os.path.exists(out_path):
            update(job_id, status="error", error_message=f"ffmpeg failed rc={rc}", logs=logs[-1000:])
            return

        output_key = f"outputs/{job_id}/output.mp4"
        upload_file(out_path, output_key)

        update(job_id, status="done", output_key=output_key, updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    except ClientError as e:
        update(job_id, status="error", error_message=str(e))
    except Exception as e:
        update(job_id, status="error", error_message=f"unexpected: {e}")
