resource "kubernetes_namespace" "oficina" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/part-of" = "tech-challenge"
    }
  }
}
