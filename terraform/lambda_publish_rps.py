import boto3, os
from datetime import datetime, timedelta, timezone

cw = boto3.client('cloudwatch')
elb = boto3.client('elbv2')

TARGET_GROUP_ARN = os.environ.get('TARGET_GROUP_ARN')  # passed in as env var
NAMESPACE = os.environ.get('METRIC_NAMESPACE', 'APP')
METRIC_NAME = os.environ.get('METRIC_NAME', 'RequestsPerSecond')

def get_request_count(tg_arn, period=60):
    end = datetime.now(timezone.utc)
    start = end - timedelta(seconds=period*2)
    resp = cw.get_metric_statistics(
        Namespace='AWS/ApplicationELB',
        MetricName='RequestCount',
        Dimensions=[{'Name': 'TargetGroup', 'Value': tg_arn}],
        StartTime=start,
        EndTime=end,
        Period=period,
        Statistics=['Sum']
    )
    dps = resp.get('Datapoints', [])
    if not dps:
        return 0.0
    latest = max(dps, key=lambda d: d['Timestamp'])
    return float(latest.get('Sum', 0.0))

def get_healthy_count(tg_arn):
    resp = elb.describe_target_health(TargetGroupArn=tg_arn)
    healthy = [t for t in resp.get('TargetHealthDescriptions', []) if t.get('TargetHealth',{}).get('State')=='healthy']
    return max(1, len(healthy))

def publish(tg_arn):
    total = get_request_count(tg_arn)
    healthy = get_healthy_count(tg_arn)
    rps_per_target = (total / 60.0) / healthy
    print(f"Publishing rps_per_target={rps_per_target} total={total} healthy={healthy}")
    cw.put_metric_data(
        Namespace=NAMESPACE,
        MetricData=[{
            'MetricName': METRIC_NAME,
            'Dimensions': [{'Name':'TargetGroup', 'Value': tg_arn}],
            'Unit': 'Count',
            'Value': rps_per_target
        }]
    )

def lambda_handler(event, context):
    if not TARGET_GROUP_ARN:
        raise Exception("TARGET_GROUP_ARN not set")
    publish(TARGET_GROUP_ARN)
    return {"status": "ok"}
