output "reports_bucket" {
  description = "S3 bucket for CI scan reports."
  value       = aws_s3_bucket.reports.bucket
}

output "ecr_repository_url" {
  description = "ECR repository URL for pushing the app image."
  value       = aws_ecr_repository.app.repository_url
}

output "alerts_topic_arn" {
  description = "SNS topic that receives build and scan failure alerts."
  value       = aws_sns_topic.alerts.arn
}

output "app_security_group_id" {
  description = "Security group attached to the app."
  value       = aws_security_group.app.id
}
