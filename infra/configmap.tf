resource "kubernetes_config_map" "app_config" {
  metadata {
    name      = "tech-challenge-config"
    namespace = kubernetes_namespace.oficina.metadata[0].name
  }

  data = {
    ALGORITHM                  = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = "60"
    ALLOWED_ORIGINS            = "[\"http://localhost:3000\"]"
    ADMIN_USERNAME             = "admin"
  }
}
