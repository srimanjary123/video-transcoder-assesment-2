from typing import Dict
import boto3
from fastapi import HTTPException
from config import AWS_REGION, DDB_TABLE

_table = boto3.resource("dynamodb", region_name=AWS_REGION).Table(DDB_TABLE)

def put_item(item: Dict):
    _table.put_item(Item=item)

def get(job_id: str) -> Dict:
    res = _table.get_item(Key={"job_id": job_id})
    if "Item" not in res:
        raise HTTPException(status_code=404, detail="Job not found")
    return res["Item"]

def update(job_id: str, **attrs):
    if not attrs:
        return
    expr = "SET " + ", ".join(f"#{k}=:{k}" for k in attrs)
    names = {f"#{k}": k for k in attrs}
    values = {f":{k}": v for k, v in attrs.items()}
    _table.update_item(
        Key={"job_id": job_id},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )
