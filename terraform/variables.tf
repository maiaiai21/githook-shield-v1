variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-south-1"
}

variable "use_localstack" {
  description = "Point the AWS provider at a LocalStack gateway instead of real AWS."
  type        = bool
  default     = true
}

variable "localstack_endpoint" {
  description = "LocalStack gateway URL, used only when use_localstack is true."
  type        = string
  default     = "http://localhost:4566"
}

variable "reports_bucket_name" {
  description = "S3 bucket that stores CI scan reports. Must be globally unique on real AWS."
  type        = string
  default     = "githook-shield-scan-reports"
}

variable "ecr_repository_name" {
  description = "ECR repository for the application image."
  type        = string
  default     = "githook-shield"
}

variable "alert_email" {
  description = "Email address subscribed to the alert topic. Leave empty to skip the subscription."
  type        = string
  default     = ""
}

variable "app_port" {
  description = "Port the Flask app listens on. Used to open the security group."
  type        = number
  default     = 5000
}

variable "allowed_cidr" {
  description = "CIDR block allowed to reach the app port."
  type        = string
  default     = "10.0.0.0/8"
}