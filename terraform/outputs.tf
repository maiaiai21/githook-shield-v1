output "app_namespace" {
  description = "Namespace containing the application."
  value       = kubernetes_namespace_v1.app.metadata[0].name
}

output "app_service" {
  description = "ClusterIP service for the Flask app."
  value       = kubernetes_service_v1.app.metadata[0].name
}

output "dashboard_service" {
  description = "ClusterIP service for the security activity dashboard."
  value       = kubernetes_service_v1.dashboard.metadata[0].name
}

output "monitoring_namespace" {
  description = "Namespace containing Prometheus and Grafana."
  value       = helm_release.monitoring.namespace
}

output "grafana_service" {
  description = "Grafana service name for kubectl port-forward."
  value       = "${helm_release.monitoring.name}-grafana"
}

output "prometheus_service" {
  description = "Prometheus service name for kubectl port-forward."
  value       = "${helm_release.monitoring.name}-kube-promet-prometheus"
}
