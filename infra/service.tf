resource "kubernetes_service" "api" {
  metadata {
    name      = "tech-challenge-svc"
    namespace = kubernetes_namespace.oficina.metadata[0].name
  }

  spec {
    type = "NodePort"

    selector = {
      app = "tech-challenge-api"
    }

    port {
      port        = 8000
      target_port = 8000
      node_port   = 30080
      protocol    = "TCP"
    }
  }
}
