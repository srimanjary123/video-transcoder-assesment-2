import boto3, os, json
session = boto3.Session(region_name=os.getenv("AWS_REGION"))
print(json.dumps(session.client("dynamodb").describe_table(TableName=os.getenv("DDB_TABLE_NAME"))["Table"]["KeySchema"], indent=2))