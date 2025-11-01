import json
import sys
import logging
import boto3
from datetime import datetime
# Configure logging to CloudWatch automatically when ECS logs are enabled
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)
def update_job_status(job_id, status):
    """
    Simulate updating job status (for example, write to DynamoDB or print to logs).
    In a real case, you would use boto3.resource('dynamodb') etc.
    """
    logger.info(f"Updating job {job_id} → status = {status}")
    # Example: Save to DynamoDB (optional)
    # dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    # table = dynamodb.Table('video-jobs')
    # table.update_item(
    #     Key={'jobId': job_id},
    #     UpdateExpression='SET jobStatus = :status, updatedAt = :time',
    #     ExpressionAttributeValues={
    #         ':status': status,
    #         ':time': datetime.utcnow().isoformat()
    #     }
    # )

def handler(event):
    """
    This function processes a single EventBridge event.
    The event JSON comes from stdin when invoked by ECS.
    """
    try:
        detail = event.get('detail', {})
        job_id = detail.get('jobId')
        status = detail.get('status')
        logger.info(f"Received event: {json.dumps(event)}")
        if job_id and status:
            update_job_status(job_id, status)
        else:
            logger.warning("Event missing jobId or status field.")
    except Exception as e:
        logger.exception(f"Error processing event: {e}")

if __name__ == "__main__":
    # ECS passes event payload via STDIN
    try:
        raw = sys.stdin.read()
        if raw:
            event = json.loads(raw)
            handler(event)
        else:
            logger.warning("No event data received.")
    except Exception as e:
        logger.exception(f"Startup error: {e}")
