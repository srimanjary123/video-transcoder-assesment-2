from fastapi import APIRouter, Depends
from app import require_jwt
from config import S3_BUCKET, DDB_TABLE

router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True, "bucket": S3_BUCKET, "table": DDB_TABLE}

@router.get("/auth/me")
def me(user=Depends(require_jwt)):
    return user
