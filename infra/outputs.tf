output "node_port" {
  description = "NodePort exposto pela API — obter a URL completa com: minikube service tech-challenge-svc -n oficina --url"
  value       = kubernetes_service.api.spec[0].port[0].node_port
}

output "namespace" {
  description = "Namespace Kubernetes criado"
  value       = kubernetes_namespace.oficina.metadata[0].name
}

output "get_url_command" {
  description = "Comando para obter a URL de acesso via minikube"
  value       = "minikube service tech-challenge-svc -n oficina --url"
}
