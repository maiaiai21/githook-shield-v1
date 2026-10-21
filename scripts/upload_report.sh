#!/bin/sh
# Upload a scan report to the reports bucket, keyed by commit and time.
#   Usage: upload_report.sh path/to/report.json
# Reads REPORTS_BUCKET and optionally AWS_ENDPOINT_URL. Skips when no bucket is set.
set -e

if [ -z "${REPORTS_BUCKET:-}" ]; then
  echo "REPORTS_BUCKET not set; skipping report upload."
  exit 0
fi

ENDPOINT_ARG=""
if [ -n "${AWS_ENDPOINT_URL:-}" ]; then
  ENDPOINT_ARG="--endpoint-url ${AWS_ENDPOINT_URL}"
fi

KEY="scans/${GITHUB_SHA:-local}/$(date -u +%Y%m%dT%H%M%SZ)-$(basename "$1")"
aws s3 cp $ENDPOINT_ARG "$1" "s3://${REPORTS_BUCKET}/${KEY}"
echo "Uploaded to s3://${REPORTS_BUCKET}/${KEY}"