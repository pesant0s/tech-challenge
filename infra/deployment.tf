resource "kubernetes_deployment" "api" {
  metadata {
    name      = "tech-challenge-api"
    namespace = kubernetes_namespace.oficina.metadata[0].name
    labels = {
      app = "tech-challenge-api"
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = "tech-challenge-api"
      }
    }

    template {
      metadata {
        labels = {
          app = "tech-challenge-api"
        }
      }

      spec {
        container {
          name              = "api"
          image             = "tech-challenge-api:${var.image_tag}"
          image_pull_policy = "Never"

          port {
            container_port = 8000
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.app_config.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.app_secret.metadata[0].name
            }
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds        = 10
            failure_threshold     = 3
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds        = 20
            failure_threshold     = 3
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }
        }
      }
    }
  }
}
