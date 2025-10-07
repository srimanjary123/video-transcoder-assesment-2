import os
import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
print("Using region:", AWS_REGION)

client = boto3.client("cognito-idp", region_name=AWS_REGION)
print("Using client:", client)

def list_pools():
    try:
        resp = client.list_user_pools(MaxResults=60)
        print("User pools:")
        for p in resp.get("UserPools", []):
            print(" - Id:", p.get("Id"), "Name:", p.get("Name"))
    except ClientError as e:
        print("Error listing user pools:", e)

def list_clients_for_pool(pool_id):
    try:
        resp = client.list_user_pool_clients(UserPoolId=pool_id, MaxResults=60)
        print(f"App clients for pool {pool_id}:")
        for c in resp.get("UserPoolClients", []):
            print(" - ClientId:", c.get("ClientId"), "ClientName:", c.get("ClientName"))
    except ClientError as e:
        print(f"Error listing clients for pool {pool_id}:", e)

if __name__ == "__main__":
    list_pools()
    # If you know your pool id put it here; otherwise run the script and copy one returned above
    # Example: list_clients_for_pool("ap-south-1_XXXX")
    # list_clients_for_pool("ap-south-1_XXXXXXXXX")
