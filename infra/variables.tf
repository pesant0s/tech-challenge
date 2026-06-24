variable "namespace" {
  description = "Namespace Kubernetes da aplicação"
  type        = string
  default     = "oficina"
}

variable "image_tag" {
  description = "Tag da imagem Docker da API"
  type        = string
  default     = "latest"
}

variable "replicas" {
  description = "Número inicial de réplicas da API"
  type        = number
  default     = 2
}

variable "secret_key" {
  description = "Chave secreta JWT (mínimo 32 chars)"
  type        = string
  sensitive   = true
  default     = "super-secret-key-minimo-32-chars-troque"
}

variable "webhook_secret" {
  description = "Segredo para validação de webhooks de e-mail"
  type        = string
  sensitive   = true
  default     = "webhook-secret-local"
}

variable "admin_password" {
  description = "Senha do usuário admin"
  type        = string
  sensitive   = true
  default     = "admin123"
}

variable "postgres_password" {
  description = "Senha do banco PostgreSQL"
  type        = string
  sensitive   = true
  default     = "oficina"
}
