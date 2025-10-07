import time
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth_cognito import require_jwt
from db_videos import put_item, get as ddb_get
from storage_s3 import presigned_put, presigned_get

router = APIRouter()

class CreateJobReq(BaseModel):
    filename: str
    content_type: Optional[str] = "video/mp4"

@router.post("/jobs")
def create_job(req: CreateJobReq, user=Depends(require_jwt)):
    job_id = str(uuid.uuid4())
    upload_key = f"uploads/{job_id}/{req.filename}"
    put_url = presigned_put(upload_key, req.content_type or "application/octet-stream")
    item = {
        "job_id": job_id,
        "user_sub": user.get("sub", ""),
        "status": "created",
        "filename_in": req.filename,
        "upload_key": upload_key,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    put_item(item)
    return {"job_id": job_id, "put_url": put_url, "s3_key": upload_key}

@router.get("/jobs/{job_id}")
def get_job(job_id: str, user=Depends(require_jwt)):
    item = ddb_get(job_id)
    if item.get("user_sub") != user.get("sub"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return item

@router.get("/jobs/{job_id}/download-url")
def get_download(job_id: str, user=Depends(require_jwt)):
    item = ddb_get(job_id)
    if item.get("user_sub") != user.get("sub"):
        raise HTTPException(status_code=403, detail="Forbidden")
    if item.get("status") != "done":
        raise HTTPException(status_code=400, detail=f"Job not done (status={item.get('status')})")
    return {"url": presigned_get(item["output_key"])}
