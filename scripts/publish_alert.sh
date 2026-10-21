#!/bin/sh
# Publish a pipeline alert to the SNS topic.
#   Usage: publish_alert.sh "subject" "message"
# Reads SNS_TOPIC_ARN from the environment. Set AWS_ENDPOINT_URL to target
# LocalStack (for example http://localhost:4566). Skips quietly when no topic is set,
# so CI runs without AWS credentials still pass.
set -e

if [ -z "${SNS_TOPIC_ARN:-}" ]; then
  echo "SNS_TOPIC_ARN not set; skipping alert."
  exit 0
fi

ENDPOINT_ARG=""
if [ -n "${AWS_ENDPOINT_URL:-}" ]; then
  ENDPOINT_ARG="--endpoint-url ${AWS_ENDPOINT_URL}"
fi

aws sns publish \
  $ENDPOINT_ARG \
  --topic-arn "$SNS_TOPIC_ARN" \
  --subject "$1" \
  --message "$2"