resource "kubernetes_namespace_v1" "app" {
  metadata {
    name = var.app_namespace
  }
}

resource "kubernetes_deployment_v1" "app" {
  metadata {
    name      = "githook-shield"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
    labels = {
      app = "githook-shield"
    }
  }

  spec {
    replicas = var.app_replicas

    selector {
      match_labels = {
        app = "githook-shield"
      }
    }

    template {
      metadata {
        labels = {
          app = "githook-shield"
        }
      }

      spec {
        container {
          name              = "flask-app"
          image             = var.app_image
          image_pull_policy = "IfNotPresent"

          port {
            name           = "http"
            container_port = 5000
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 5000
            }
            initial_delay_seconds = 5
            period_seconds        = 10
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 5000
            }
            initial_delay_seconds = 15
            period_seconds        = 20
          }

          resources {
            requests = {
              cpu    = "50m"
              memory = "64Mi"
            }
            limits = {
              cpu    = "250m"
              memory = "128Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "app" {
  metadata {
    name      = "githook-shield"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  spec {
    selector = {
      app = "githook-shield"
    }

    port {
      name        = "http"
      port        = 80
      target_port = 5000
    }

    type = "ClusterIP"
  }
}

resource "kubernetes_config_map_v1" "dashboard_data" {
  metadata {
    name      = "githook-shield-dashboard-data"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  data = {
    "scan-log.json" = fileexists("${path.module}/../scan-log.json") ? file("${path.module}/../scan-log.json") : ""
    "results.json"  = file("${path.module}/../evaluation/results.json")
  }
}

resource "kubernetes_deployment_v1" "dashboard" {
  metadata {
    name      = "githook-shield-dashboard"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
    labels = {
      app = "githook-shield-dashboard"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "githook-shield-dashboard"
      }
    }

    template {
      metadata {
        labels = {
          app = "githook-shield-dashboard"
        }
      }

      spec {
        container {
          name              = "dashboard"
          image             = var.dashboard_image
          image_pull_policy = "IfNotPresent"

          port {
            name           = "http"
            container_port = 80
          }

          readiness_probe {
            http_get {
              path = "/dashboard/"
              port = 80
            }
            initial_delay_seconds = 2
            period_seconds        = 5
          }

          liveness_probe {
            http_get {
              path = "/dashboard/"
              port = 80
            }
            initial_delay_seconds = 5
            period_seconds        = 10
          }

          resources {
            requests = {
              cpu    = "10m"
              memory = "16Mi"
            }
            limits = {
              cpu    = "100m"
              memory = "64Mi"
            }
          }

          volume_mount {
            name       = "dashboard-data"
            mount_path = "/usr/share/nginx/html/scan-log.json"
            sub_path   = "scan-log.json"
            read_only  = true
          }

          volume_mount {
            name       = "dashboard-data"
            mount_path = "/usr/share/nginx/html/evaluation/results.json"
            sub_path   = "results.json"
            read_only  = true
          }
        }

        volume {
          name = "dashboard-data"

          config_map {
            name = kubernetes_config_map_v1.dashboard_data.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "dashboard" {
  metadata {
    name      = "githook-shield-dashboard"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  spec {
    selector = {
      app = "githook-shield-dashboard"
    }

    port {
      name        = "http"
      port        = 80
      target_port = 80
    }

    type = "ClusterIP"
  }
}

resource "helm_release" "monitoring" {
  name             = "githook-shield"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = var.monitoring_chart_version
  namespace        = var.monitoring_namespace
  create_namespace = true
  wait             = true
  timeout          = 600
  cleanup_on_fail  = true

  values = [
    file("${path.module}/monitoring-values.yaml")
  ]
}
