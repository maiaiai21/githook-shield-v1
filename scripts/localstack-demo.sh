#!/bin/sh
# End-to-end local demo of Phase 3 against LocalStack.
#   1. Start LocalStack
#   2. Create the AWS resources with Terraform
#   3. Upload a sample scan report to S3
#   4. Publish a sample alert to SNS
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export AWS_ENDPOINT_URL="http://localhost:4566"
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="ap-south-1"

echo "== Starting LocalStack"
docker compose -f "$ROOT/docker-compose.yml" up -d
echo "Waiting for LocalStack..."
until curl -sf "$AWS_ENDPOINT_URL/_localstack/health" >/dev/null; do sleep 2; done

echo "== Creating AWS resources with Terraform"
cd "$ROOT/terraform"
terraform init -input=false
terraform apply -input=false -auto-approve
REPORTS_BUCKET=$(terraform output -raw reports_bucket)
SNS_TOPIC_ARN=$(terraform output -raw alerts_topic_arn)
cd "$ROOT"

echo "== Uploading a sample scan report"
echo '{"tool": "secretscan", "findings": 1}' > /tmp/sample-report.json
REPORTS_BUCKET="$REPORTS_BUCKET" sh "$ROOT/scripts/upload_report.sh" /tmp/sample-report.json

echo "== Publishing a sample alert"
SNS_TOPIC_ARN="$SNS_TOPIC_ARN" sh "$ROOT/scripts/publish_alert.sh" \
  "GitHook Shield: demo alert" "Sample alert from localstack-demo.sh"

echo "== Done. Check with:"
echo "   aws --endpoint-url \$AWS_ENDPOINT_URL s3 ls s3://$REPORTS_BUCKET --recursive"