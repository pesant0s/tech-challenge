output "service_url" {
  description = "URL de acesso à API via NodePort (usar com: minikube service tech-challenge-svc -n oficina --url)"
  value       = "http://$(minikube ip):30080"
}

output "namespace" {
  description = "Namespace Kubernetes criado"
  value       = kubernetes_namespace.oficina.metadata[0].name
}

output "swagger_url" {
  description = "URL do Swagger UI (após obter IP do minikube)"
  value       = "http://$(minikube ip):30080/docs"
}
