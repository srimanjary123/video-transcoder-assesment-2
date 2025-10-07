"""
DynamoDB wrapper for jobs table.
"""
from typing import Dict
import time
import boto3
from fastapi import HTTPException
from config import settings

_table = boto3.resource("dynamodb", region_name=settings.AWS_REGION).Table(settings.DDB_TABLE)

def ddb_put(item: Dict):
    if "created_at" not in item:
        item["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _table.put_item(Item=item)

def ddb_get(job_id: str) -> Dict:
    res = _table.get_item(Key={"job_id": job_id})
    if "Item" not in res:
        raise HTTPException(status_code=404, detail="Job not found")
    return res["Item"]

def ddb_update(job_id: str, **attrs):
    if not attrs:
        return
    expr = "SET " + ", ".join(f"#{k}=:{k}" for k in attrs)
    names = {f"#{k}": k for k in attrs}
    values = {f":{k}": v for k, v in attrs.items()}
    _table.update_item(Key={"job_id": job_id}, UpdateExpression=expr,
                       ExpressionAttributeNames=names, ExpressionAttributeValues=values)
