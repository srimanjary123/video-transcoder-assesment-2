import boto3
from config import AWS_REGION, S3_BUCKET

_s3 = boto3.client("s3", region_name=AWS_REGION)

def presigned_put(key: str, content_type: str, expires: int = 900) -> str:
    return _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": S3_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )

def presigned_get(key: str, expires: int = 900) -> str:
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )

def download_file(key: str, local_path: str):
    _s3.download_file(S3_BUCKET, key, local_path)

def upload_file(local_path: str, key: str):
    _s3.upload_file(local_path, S3_BUCKET, key)
