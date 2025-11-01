// index.mjs (Node 20 supports ES modules by default)
import { DynamoDBClient, UpdateItemCommand } from "@aws-sdk/client-dynamodb";
import { SNSClient, PublishCommand } from "@aws-sdk/client-sns";

const ddb = new DynamoDBClient({});
const sns = new SNSClient({});
const TABLE = process.env.DDB_JOBS_TABLE;
const NOTIFY = process.env.NOTIFY_TOPIC_ARN;

export const handler = async (event) => {
  const failures = [];

  for (const r of event.Records ?? []) {
    try {
      const body = safeJSON(r.body);
      const jobId = body?.jobId || body?.id || inferJobIdFromBody(body, r.messageId);

      // Mark job failed with context from the dead-letter
      if (jobId && TABLE) {
        const errorMsg = buildError(body, r);
        await ddb.send(new UpdateItemCommand({
          TableName: TABLE,
          Key: { id: { S: jobId } },
          UpdateExpression: "SET #status = :failed, #error = :err, #updatedAt = :now",
          ExpressionAttributeNames: { "#status": "status", "#error": "error", "#updatedAt": "updatedAt" },
          ExpressionAttributeValues: {
            ":failed": { S: "failed" },
            ":err":    { S: errorMsg },
            ":now":    { S: new Date().toISOString() }
          }
        }));
      }

      // Optional notify
      if (NOTIFY) {
        await sns.send(new PublishCommand({
          TopicArn: NOTIFY,
          Subject: `DLQ: job failed ${jobId ?? ""}`.trim(),
          Message: JSON.stringify({ jobId, record: r, body }, null, 2)
        }));
      }
    } catch (e) {
      console.error("DLQ handler error for messageId", r.messageId, e);
      failures.push({ itemIdentifier: r.messageId }); // tell SQS to retry this record later
    }
  }

  // Partial-batch response so only failed records are retried
  return { batchItemFailures: failures };
};

function safeJSON(s) { try { return JSON.parse(s); } catch { return null; } }
function inferJobIdFromBody(body, fallback) {
  // Your messages usually include jobId; keep this as a fallback
  return body?.params?.jobId || body?.job?.id || fallback;
}
function buildError(body, r) {
  const basic = `Message moved to DLQ after max receives.`;
  return `${basic} LastBody=${JSON.stringify(body)} ApproxReceiveCount=${r.attributes?.ApproximateReceiveCount || "?"}`;
}