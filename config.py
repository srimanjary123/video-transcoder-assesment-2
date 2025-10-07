"""
Central config used by app.py.
You can still override with environment variables in EC2.
"""
import os

class Settings:
    AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
    S3_BUCKET = os.getenv("S3_BUCKET", "n10886524-assessment2")
    DDB_TABLE = os.getenv("DDB_TABLE", "n10886524-jobs")
    COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "ap-southeast-2_6v2d6FsVv")
    COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "23jdip77jlkikbnoddnktp89b7n")
    CORS_ALLOWED = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS","").split(",") if o.strip()] or ["*"]

settings = Settings()
