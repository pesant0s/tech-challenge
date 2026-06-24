resource "kubernetes_secret" "app_secret" {
  metadata {
    name      = "tech-challenge-secret"
    namespace = kubernetes_namespace.oficina.metadata[0].name
  }

  type = "Opaque"

  data = {
    DATABASE_URL   = "postgresql://oficina:${var.postgres_password}@postgres-svc:5432/oficina"
    SECRET_KEY     = var.secret_key
    WEBHOOK_SECRET = var.webhook_secret
    ADMIN_PASSWORD = var.admin_password
  }
}
