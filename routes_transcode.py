from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel

from auth_cognito import require_jwt
from db_videos import get as ddb_get
from services_transcode import transcode_task

router = APIRouter()

class StartJobReq(BaseModel):
    s3_key: Optional[str] = None
    target_preset: Optional[str] = "480p"   # ["360p","480p","720p"]

@router.post("/jobs/{job_id}/start")
def start_job(job_id: str, req: StartJobReq, bg: BackgroundTasks, user=Depends(require_jwt)):
    item = ddb_get(job_id)
    if item.get("user_sub") != user.get("sub"):
        raise HTTPException(status_code=403, detail="Forbidden")
    input_key = req.s3_key or item.get("upload_key")
    if not input_key:
        raise HTTPException(status_code=400, detail="Missing s3_key; create job first")
    bg.add_task(transcode_task, job_id, input_key, req.target_preset or "480p")
    return {"ok": True, "message": "Processing started"}
