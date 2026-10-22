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
