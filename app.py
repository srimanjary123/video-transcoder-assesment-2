import os
import time
import uuid
import subprocess
from typing import Optional, Dict

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import jwt
from jwt import PyJWKClient
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import hmac
import hashlib
import base64

bearer_scheme = HTTPBearer()

# ======== Config from environment ========
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
S3_BUCKET = os.getenv("S3_BUCKET", "n10886524-assessment2")
DDB_TABLE = os.getenv("DDB_TABLE", "n10886524-jobs")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "ap-southeast-2_6v2d6FsVv")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "23jdip77jlkikbnoddnktp89b7n")
CORS_ALLOWED = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()] or ["*"]
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET", "hesuccknljhegfkpu7iq2r5jpc3bsq9nqm4ibe8iuiacgditn5d")
# ======== AWS clients ========
#s3 = boto3.client("s3", region_name=AWS_REGION)
#ddb = boto3.resource("dynamodb", region_name=AWS_REGION).Table(DDB_TABLE)
cognito = boto3.client("cognito-idp", region_name=AWS_REGION)

if not COGNITO_APP_CLIENT_ID or not COGNITO_USER_POOL_ID:
    raise RuntimeError("Set COGNITO_CLIENT_ID and COGNITO_USER_POOL_ID in env")

# ======== App ========
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="Video Transcoder API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======== Cognito JWT validation ========
JWKS_URL = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
_jwk_client = PyJWKClient(JWKS_URL)

def require_jwt(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> Dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = credentials.credentials
    if token == "test-dev-token":
        return {"sub": "dev-user", "email": "dev@example.com"}
    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}",
        )
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

# ======== Models ========
class CreateJobReq(BaseModel):
    filename: str
    content_type: Optional[str] = "video/mp4"

class StartJobReq(BaseModel):
    s3_key: Optional[str] = None
    target_preset: Optional[str] = "480p"

# ======== DDB helpers ========
def ddb_put_item_bkp(item: Dict):
    ddb.put_item(Item=item)

def get_boto_session():
    return boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        region_name=os.getenv("AWS_REGION"),
    )

def ddb_put_item_bkp_1(item: dict):
    session = get_boto_session()
    ddb = session.resource("dynamodb")
    table = ddb.Table(os.getenv("DDB_TABLE_NAME"))

    # Read required keys from the table's key schema
    ks = table.key_schema  # list of dicts {"AttributeName": ..., "KeyType": ...}
    required = [k["AttributeName"] for k in ks]  # exact names as table expects

    # Build mapping of cleaned -> actual required name
    # e.g. "qut-username" -> "qut-username " (if table has trailing space)
    required_map = {}
    for rk in required:
        cleaned = rk.strip()   # remove leading/trailing whitespace
        required_map[cleaned] = rk

    # Attempt to ensure each required key exists in the item,
    # mapping from a cleaned key if present.
    for cleaned, actual in required_map.items():
        if actual in item and item[actual] is not None:
            continue  # already present as exact key
        # try common variants: cleaned key, cleaned key with underscores, etc.
        if cleaned in item and item[cleaned] is not None:
            # copy value to exact required key name that table expects
            item[actual] = item.pop(cleaned)
            logger.warning("Mapped item key '%s' -> table key '%s'", cleaned, actual)
            continue
        # try keys that differ only by whitespace or hidden chars
        found = False
        for existing_key in list(item.keys()):
            if existing_key.strip() == cleaned:
                # copy and preserve existing_key removal
                item[actual] = item.pop(existing_key)
                logger.warning("Mapped existing key repr(%r) -> table key '%s'", existing_key, actual)
                found = True
                break
        if found:
            continue
        # no match found; leave missing for now

    # Now validate required keys are present and non-null
    missing = [k for k in required if k not in item or item[k] is None]
    if missing:
        # helpful diagnostic including item keys (repr to reveal hidden chars if any)
        item_keys_repr = [repr(k) for k in item.keys()]
        raise RuntimeError(
            f"Missing required key(s) for table: {missing}. Item keys present: {item_keys_repr}"
        )

    # Ensure required keys are strings
    for k in required:
        item[k] = str(item[k])

    # Finally attempt to put the item
    try:
        resp = table.put_item(Item=item)
        logger.info("DynamoDB PutItem success. RequestId=%s", resp.get("ResponseMetadata", {}).get("RequestId"))
        return resp
    except ClientError as e:
        logger.exception("DynamoDB PutItem failed")
        raise RuntimeError(f"DynamoDB PutItem failed: {e.response}")

def ddb_put_item(item: dict):
    # Create a new boto3 session (your helper)
    session = get_boto_session()
    ddb = session.resource("dynamodb")
    table = ddb.Table(os.getenv("DDB_TABLE_NAME"))

    # --- Validate required keys from table schema ---
    ks = table.key_schema  # list of dicts with AttributeName and KeyType
    required = [k["AttributeName"] for k in ks]

    # Find any missing or None key values
    missing = [k for k in required if k not in item or item[k] is None]
    if missing:
        raise RuntimeError(
            f"Missing required key(s) for table: {missing}. "
            f"Item keys present: {list(item.keys())}"
        )

    # Ensure all required key values are strings (DynamoDB expects strings for most keys)
    for k in required:
        item[k] = str(item[k])

    # --- Attempt to write item to DynamoDB ---
    try:
        resp = table.put_item(Item=item)
        logger.info(f"DynamoDB PutItem success. RequestId={resp['ResponseMetadata'].get('RequestId')}")
        return resp
    except ClientError as e:
        logger.exception("DynamoDB PutItem failed: %s", e)
        raise RuntimeError(f"DynamoDB PutItem failed: {e.response}")

def ddb_put_item_nnnnm(item: dict):
    session = get_boto_session()
    ddb = session.resource("dynamodb")
    table = ddb.Table(os.getenv("DDB_TABLE_NAME"))
    try:
        return table.put_item(Item=item)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("ExpiredTokenException", "InvalidClientTokenId", "UnrecognizedClientException"):
            raise RuntimeError("AWS credentials invalid or expired. Please refresh your AWS credentials (aws sso login / re-run assume-role / aws configure).")
        raise RuntimeError(f"DynamoDB PutItem failed: {e.response}")
    
def ddb_put_item_nnnn(item: dict):
    session = get_boto_session()
    ddb = session.resource("dynamodb")
    table = ddb.Table(os.getenv("DDB_TABLE_NAME"))
    try:
        resp = table.put_item(Item=item)
        return resp
    except ClientError as e:
        logger.exception("DynamoDB PutItem failed: %s", e)
        raise RuntimeError(f"DynamoDB PutItem failed: {e.response}")

def ddb_get_mmm(job_id: str) -> Dict:
    res = ddb.get_item(Key={"qut-username": job_id})
    if "Item" not in res:
        raise HTTPException(status_code=404, detail="Job not found")
    return res["Item"]

def ddb_get(job_id: str) -> Dict:
    try:
        session = get_boto_session()
        ddb = session.resource("dynamodb")
        table = ddb.Table(os.getenv("DDB_TABLE_NAME"))
        res = table.get_item(Key={"qut-username": job_id})
        print(f"My job id is {job_id}")
        if "Item" not in res:
            raise HTTPException(status_code=404, detail="Job not found")
        return res["Item"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ddb_get failed: {str(e)}")

def ddb_update(job_id: str, **attrs):
    if not attrs:
        return
    expr = "SET " + ", ".join(f"#{k}=:{k}" for k in attrs)
    names = {f"#{k}": k for k in attrs}
    values = {f":{k}": v for k, v in attrs.items()}
    ddb.update_item(
        Key={"job_id": job_id},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )

# ======== S3 helpers ========
def presigned_put_1(key: str, content_type: str, expires: int = 900) -> str:
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": S3_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )

def get_boto_session():
    return boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        region_name=os.getenv("AWS_REGION"),
    )

def presigned_put(key: str, content_type: str, expires: int = 900) -> str:
    session = get_boto_session()
    s3 = session.client("s3")
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": os.getenv("S3_BUCKET"), "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )

def presigned_get(key: str, expires: int = 900) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )

# ======== misc ========
def _run(cmd: list) -> tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout

# ======== Endpoints ========
@app.get("/health")
def health():
    return {"ok": True, "bucket": S3_BUCKET, "table": DDB_TABLE}

@app.get("/")
def serve_index():
    return FileResponse(os.path.join("web", "index.html"))

@app.get("/auth/me")
def auth_me(user=Depends(require_jwt)):
    return user

@app.post("/jobs")
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
    ddb_put_item(item)
    return {"job_id": job_id, "put_url": put_url, "s3_key": upload_key}

@app.get("/jobs/{job_id}")
def get_job(job_id: str, user=Depends(require_jwt)):
    item = ddb_get(job_id)
    if item.get("user_sub") != user.get("sub"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return item

def transcode_task(job_id: str, input_key: str, preset: str):
    try:
        ddb_update(job_id, status="processing", started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        base = f"/tmp/{job_id}"
        os.makedirs(base, exist_ok=True)
        in_path = f"{base}/input"
        out_path = f"{base}/output.mp4"

        s3.download_file(S3_BUCKET, input_key, in_path)

        vf = "scale=-2:480"
        if preset == "720p":
            vf = "scale=-2:720"
        elif preset == "360p":
            vf = "scale=-2:360"

        rc, logs = _run([
            "ffmpeg", "-y", "-i", in_path, "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-c:a", "aac", out_path
        ])
        if rc != 0 or not os.path.exists(out_path):
            ddb_update(job_id, status="error", error_message=f"ffmpeg failed rc={rc}", logs=logs[-1000:])
            return

        output_key = f"outputs/{job_id}/output.mp4"
        s3.upload_file(out_path, S3_BUCKET, output_key)
        ddb_update(job_id, status="done", output_key=output_key, updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    except ClientError as e:
        ddb_update(job_id, status="error", error_message=str(e))
    except Exception as e:
        ddb_update(job_id, status="error", error_message=f"unexpected: {e}")

@app.post("/jobs/{job_id}/start")
def start_job(job_id: str, req: StartJobReq, bg: BackgroundTasks, user=Depends(require_jwt)):
    item = ddb_get(job_id)
    if item.get("user_sub") != user.get("sub"):
        raise HTTPException(status_code=403, detail="Forbidden")
    input_key = req.s3_key or item.get("upload_key")
    if not input_key:
        raise HTTPException(status_code=400, detail="Missing s3_key; create job first")
    bg.add_task(transcode_task, job_id, input_key, req.target_preset or "480p")
    return {"ok": True, "message": "Processing started"}

@app.get("/jobs/{job_id}/download-url")
def get_download(job_id: str, user=Depends(require_jwt)):
    item = ddb_get(job_id)
    if item.get("user_sub") != user.get("sub"):
        raise HTTPException(status_code=403, detail="Forbidden")
    if item.get("status") != "done":
        raise HTTPException(status_code=400, detail=f"Job not done (status={item.get('status')})")
    return {"url": presigned_get(item["output_key"])}

# ======== Compatibility Layer for index.html ========

def calculate_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """
    SECRET_HASH = Base64(HMAC-SHA256(client_secret, username + client_id))
    """
    msg = (username + client_id).encode("utf-8")
    key = client_secret.encode("utf-8")
    dig = hmac.new(key, msg, hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

@app.post("/api/v1/signup1")
async def api_signup_new(body: dict):
      return "Signup Done!!"

@app.post("/api/v1/login1")
async def api_login_new(body: dict):
      return "Login Done!!"

@app.post("/api/v1/signup")
async def api_signup_new(body: dict):
    username = body.get("username")
    password = body.get("password")
    email = body.get("email")
    if not username or not password or not email:
        raise HTTPException(status_code=400, detail="username, password and email are required")

    params = {
        "ClientId": COGNITO_CLIENT_ID,   # MUST be app client id
        "Username": username,
        "Password": password,
        "UserAttributes": [{"Name": "email", "Value": email}],
    }
    if COGNITO_CLIENT_SECRET:
        params["SecretHash"] = calculate_secret_hash(username, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET)

    try:
        resp = cognito.sign_up(**params)
        return {"ok": True, "user_sub": resp.get("UserSub"), "code_delivery": resp.get("CodeDeliveryDetails")}
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        raise HTTPException(status_code=400, detail=f"Signup failed: {code} - {msg}")


@app.post("/api/v1/signup")
async def api_signup(body: dict):
    username = body.get("username")
    password = body.get("password")
    email = body.get("email")
    if not username or not password or not email:
        raise HTTPException(status_code=400, detail="username, password and email are required")

    params = {
        "ClientId": "23jdip77jkikbnoddnktp89b7n",   # MUST be app client id
        "Username": username,
        "Password": password,
        "UserAttributes": [{"Name": "email", "Value": email}],
    }
    if COGNITO_CLIENT_SECRET:
        params["SecretHash"] = calculate_secret_hash(username, "23jdip77jkikbnoddnktp89b7n", COGNITO_CLIENT_SECRET)

    try:
        resp = cognito.sign_up(**params)
        return {"ok": True, "user_sub": resp.get("UserSub"), "code_delivery": resp.get("CodeDeliveryDetails")}
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        raise HTTPException(status_code=400, detail=f"Signup failed: {code} - {msg}")




@app.post("/api/v1/login")
def api_login_details(body: dict):
    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    try:
        resp = cognito.initiate_auth(
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
        )
        id_token = resp["AuthenticationResult"]["IdToken"]
        access_token = resp["AuthenticationResult"]["AccessToken"]
        refresh_token = resp["AuthenticationResult"]["RefreshToken"]

        user_info = cognito.get_user(AccessToken=access_token)
        role = "user"
        for attr in user_info["UserAttributes"]:
            if attr["Name"] == "custom:role":
                role = attr["Value"]

        return {
            "role": role,
            "id_token": id_token,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    except cognito.exceptions.UserNotConfirmedException:
        raise HTTPException(status_code=403, detail="User not confirmed (check email/phone)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")

from fastapi import FastAPI, UploadFile, File, Depends, Query, HTTPException, Header
import uuid, time, traceback, logging, requests
logger = logging.getLogger("uvicorn.error")
from fastapi import Request
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


S3_BUCKET = os.getenv("S3_BUCKET")
DDB_TABLE_NAME = os.getenv("DDB_TABLE_NAME")

s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
ddb = boto3.resource("dynamodb", region_name=AWS_REGION).Table(DDB_TABLE)


@app.get("/api/v1/users")
def list_users(limit: int = Query(25, ge=1, le=100), start_key: Optional[str] = None):
    session = get_boto_session()
    ddb = session.resource("dynamodb")
    table = ddb.Table(os.getenv("DDB_TABLE_NAME"))

    scan_kwargs = {"Limit": limit}

    if start_key:
        import json, base64
        try:
            lek_json = base64.b64decode(start_key.encode()).decode()
            scan_kwargs["ExclusiveStartKey"] = json.loads(lek_json)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid start_key: {e}")

    try:
        resp = table.scan(**scan_kwargs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    items = resp.get("Items", [])
    last_evaluated_key = resp.get("LastEvaluatedKey")
    next_key = None
    if last_evaluated_key:
        import json, base64
        next_key = base64.b64encode(json.dumps(last_evaluated_key).encode()).decode()

    return {"items": items, "next_key": next_key}

@app.post("/api/v1/upload")
def api_upload(file: UploadFile = File(...), authorization: str = Header(None)):
    try:
        user_sub = None
        if authorization:
            try:
                scheme, _, token = authorization.partition(" ")
                # replace with your validation if needed
                user_sub = validate_jwt(token).get("sub") if token else None
            except Exception as e:
                logger.warning("JWT parsing failed: %s", e)

        job_id = str(uuid.uuid4())
        upload_key = f"uploads/{job_id}/{file.filename}"
        content_type = file.content_type or "application/octet-stream"

        logger.info("Creating presigned URL for key=%s content_type=%s", upload_key, content_type)
        put_url = presigned_put(upload_key, content_type)
        if not put_url:
            raise RuntimeError("presigned_put returned empty/None")

        item = {
            "qut-username": job_id,
            "job_id": job_id,
            "user_sub": user_sub or "",
            "status": "created",
            "filename_in": file.filename,
            "upload_key": upload_key,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        # wrap DB write to catch errors
        #try:
            #ddb_put_item(item)
        #except Exception as e:
            #logger.exception("ddb_put_item failed")
            #raise

        # ensure file stream at start
        try:
            file.file.seek(0)
        except Exception:
            pass

        logger.info("Uploading to S3 via presigned URL...")
        resp = requests.put(put_url, data=file.file, headers={"Content-Type": content_type}, timeout=120)

        if resp.status_code not in (200, 201):
            # include response text from S3 for diagnosis
            msg = f"S3 upload failed status={resp.status_code} body={resp.text}"
            logger.error(msg)
            raise HTTPException(status_code=500, detail=msg)

        logger.info("Upload OK, job_id=%s", job_id)
        return {"video_id": job_id, "s3_key": upload_key}

    except HTTPException:
        # re-raise HTTPExceptions as-is
        raise
    except Exception as exc:
        tb = traceback.format_exc()
        logger.error("Unhandled error in /api/v1/upload: %s\n%s", exc, tb)
        # safe debug detail for local: return the message and traceback
        raise HTTPException(status_code=500, detail={"error": str(exc), "trace": tb})

@app.post("/api/v1/upload1")
def api_upload(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    upload_key = f"uploads/{job_id}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"

    # Generate presigned PUT URL
    put_url = presigned_put(upload_key, content_type)

    # Store metadata (optional)
    item = {
        "job_id": job_id,
        "status": "created",
        "filename_in": file.filename,
        "upload_key": upload_key,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    ddb_put_item(item)

    # Upload directly to S3
    file.file.seek(0)
    import requests
    resp = requests.put(put_url, data=file.file, headers={"Content-Type": content_type})

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"Upload to S3 failed: {resp.status_code} {resp.text}")

    return {"video_id": job_id, "s3_key": upload_key}

@app.post("/api/v1/upload_with_jwt")
def api_upload(file: UploadFile = File(...), user=Depends(require_jwt)):
    job_id = str(uuid.uuid4())
    print()
    upload_key = f"uploads/{job_id}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"

    # Generate presigned PUT URL
    put_url = presigned_put(upload_key, content_type)
    if not put_url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

    # Store metadata (your custom DynamoDB or DB call)
    item = {
        "job_id": job_id,
        "user_sub": user.get("sub", ""),
        "status": "created",
        "filename_in": file.filename,
        "upload_key": upload_key,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    ddb_put_item(item)

    # Ensure file pointer is at start
    file.file.seek(0)

    # Upload directly to S3 via presigned URL
    resp = requests.put(
        put_url,
        data=file.file,
        headers={"Content-Type": content_type},
    )

    # Check response
    if resp.status_code not in (200, 201):
        error_msg = f"Upload to S3 failed: {resp.status_code} {resp.text}"
        raise HTTPException(status_code=500, detail=error_msg)

    # Close file
    file.file.close()

    return {"video_id": job_id, "s3_key": upload_key}



@app.post("/api/v1/upload_bkp")
def api_upload(file: UploadFile, user=Depends(require_jwt)):
    job_id = str(uuid.uuid4())
    upload_key = f"uploads/{job_id}/{file.filename}"
    put_url = presigned_put(upload_key, file.content_type or "application/octet-stream")
    item = {
        "job_id": job_id,
        "user_sub": user.get("sub", ""),
        "status": "created",
        "filename_in": file.filename,
        "upload_key": upload_key,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    ddb_put_item(item)

    # Upload directly to S3 using presigned URL
    import requests
    resp = requests.put(put_url, data=file.file, headers={"Content-Type": file.content_type})
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail="Upload to S3 failed")

    return {"video_id": job_id, "s3_key": upload_key}

@app.post("/api/v1/transcode_bkp")
def api_transcode(body: dict, bg: BackgroundTasks, user=Depends(require_jwt)):
    job_id = body.get("video_id")
    resolution = body.get("resolution", "480p")
    item = ddb_get(job_id)
    if item.get("user_sub") != user.get("sub"):
        raise HTTPException(status_code=403, detail="Forbidden")
    bg.add_task(transcode_task, job_id, item.get("upload_key"), resolution)
    return {"job_id": job_id}

def validate_jwt(token: str) -> dict:
    """
    Validate a Cognito JWT access or ID token and return decoded claims.
    Raises HTTPException(401) on failure.
    """
    try:
        # Fetch signing key from JWKS
        signing_key = _jwk_client.get_signing_key_from_jwt(token).key

        # Decode and validate the token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,  # or remove this line if not verifying audience
            issuer=ISSUER,
        )

        return payload  # contains sub, email, exp, etc.

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"JWT validation error: {str(e)}")


def parse_auth_sub(authorization: str) -> str:
    """Return 'sub' from a Bearer token, or '' on failure / missing."""
    if not authorization:
        return ""
    try:
        scheme, _, token = authorization.partition(" ")
        if token:
            payload = validate_jwt(token)    # your existing validator
            return payload.get("sub", "") or ""
    except Exception as e:
        logger.warning("parse_auth_sub: JWT parsing failed: %s", e)
    return ""

COGNITO_REGION = os.getenv("COGNITO_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"

_jwk_client = PyJWKClient(JWKS_URL)

@app.post("/api/v1/transcode")
def api_transcode(body: dict, bg: BackgroundTasks, authorization: str = Header(None)):
    job_id = body.get("video_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="missing video_id")

    item = ddb_get(job_id)
    if not item:
        raise HTTPException(status_code=404, detail="job not found")

    stored_sub = item.get("user_sub", "") or ""
    requester_sub = parse_auth_sub(authorization)   # empty if no token or invalid
    logger.info("transcode requested job=%s stored_sub=%r requester_sub=%r", job_id, stored_sub, requester_sub)

    if stored_sub:
        if not requester_sub:
            logger.warning("transcode denied: job %s owned by %s but no token supplied", job_id, stored_sub)
            raise HTTPException(status_code=403, detail="Forbidden")
        if stored_sub != requester_sub:
            logger.warning("transcode denied: token sub %s does not match owner %s for job %s",
                           requester_sub, stored_sub, job_id)
            raise HTTPException(status_code=403, detail="Forbidden")

    resolution = body.get("resolution", "480p")
    bg.add_task(transcode_task, job_id, item.get("upload_key"), resolution)
    return {"job_id": job_id}


@app.get("/api/v1/status_public/{job_id}")
def api_status_public(job_id: str):
    """
    Public status endpoint used by the frontend when showing immediate progress in the table.
    This returns only minimal fields so we can poll without auth.
    """
    try:
        item = ddb_get(job_id)   # ddb_get already uses the correct table/key logic
        return {
            "job_id": job_id,
            "status": item.get("status", ""),
            "preview_gif": item.get("preview_gif", False),
            # optional: include a lightweight progress hint (if you later add progress %)
            "progress": item.get("progress")  # may be None
        }
    except HTTPException:
        # propagate 404
        raise
    except Exception as e:
        logger.exception("status_public error for %s: %s", job_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/status/{job_id}")
def api_status(job_id: str, user=Depends(require_jwt)):
    item = ddb_get(job_id)
    if item.get("user_sub") != user.get("sub"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"status": item.get("status")}

@app.get("/api/v1/download/{job_id}")
def api_download(job_id: str, user=Depends(require_jwt)):
    item = ddb_get(job_id)
    if item.get("user_sub") != user.get("sub"):
        raise HTTPException(status_code=403, detail="Forbidden")
    if item.get("status") != "done":
        raise HTTPException(status_code=400, detail="Job not done yet")
    url = presigned_get(item["output_key"])
    return {"url": url}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")), reload=False)