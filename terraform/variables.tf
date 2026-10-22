variable "kubeconfig_path" {
  description = "Path to the kubeconfig used to connect Terraform to Minikube."
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Kubernetes context to manage."
  type        = string
  default     = "minikube"
}

variable "app_namespace" {
  description = "Kubernetes namespace for the application."
  type        = string
  default     = "githook-shield"
}

variable "app_image" {
  description = "Docker image already loaded into the Minikube cluster."
  type        = string
  default     = "githook-shield:dev"
}

variable "dashboard_image" {
  description = "Docker image for the security activity dashboard, loaded into Minikube."
  type        = string
  default     = "githook-shield-dashboard:dev-live-config"
}

variable "app_replicas" {
  description = "Number of application pods."
  type        = number
  default     = 1

  validation {
    condition     = var.app_replicas >= 1
    error_message = "app_replicas must be at least 1."
  }
}

variable "monitoring_namespace" {
  description = "Kubernetes namespace for Prometheus and Grafana."
  type        = string
  default     = "monitoring"
}

variable "monitoring_chart_version" {
  description = "Pinned kube-prometheus-stack Helm chart version."
  type        = string
  default     = "69.8.2"
}
