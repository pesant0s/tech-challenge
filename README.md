# Tech Challenge — Oficina Mecânica API

Sistema de gestão de ordens de serviço para oficinas mecânicas — **Fase 2: Arquitetura Hexagonal + Infraestrutura**.

[![CI](https://github.com/pesant0s/tech-challenge/actions/workflows/ci.yml/badge.svg)](https://github.com/pesant0s/tech-challenge/actions/workflows/ci.yml)

> Pós-Tech Software Architecture — FIAP

---

## Arquitetura Hexagonal (Ports & Adapters)

```
┌─────────────────────────────────────────────────────────────────┐
│                        INBOUND ADAPTERS                         │
│  atendimento_routes · cadastro_routes · catalogo_routes         │
│  estoque_routes · auth_routes · webhook_routes                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │ chama Ports de entrada
┌─────────────────────▼───────────────────────────────────────────┐
│                     APPLICATION (Use Cases)                      │
│  CriarOS · ListarOS · AtualizarStatus · AprovarOS · RejeitarOS  │
│  ProcessarWebhookEmail · GerenciarCatalogo · GerenciarEstoque   │
│  GerenciarClientes · GerenciarVeiculos                          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                       DOMAIN                            │    │
│  │  OrdemDeServico · Cliente · Veiculo · Peca · Servico    │    │
│  │  StatusOS (máquina de estados) · CpfCnpj · Placa        │    │
│  │  NotFoundException · BusinessRuleException               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────────┘
                      │ chama Ports de saída
┌─────────────────────▼───────────────────────────────────────────┐
│                     OUTBOUND ADAPTERS                            │
│  Persistência: OSRepository · ClienteRepository · VeiculoRepo    │
│  CatalogoRepository · EstoqueRepository (SQLAlchemy 2.0)          │
│  Notificação: EmailSimuladoAdapter  ⇢ EmailNotificacaoPort        │
│  (mapeamento ORM imperativo — domínio permanece puro)            │
└─────────────────────────────────────────────────────────────────┘
```

**Regra de Dependência:** as entidades de domínio são **Python puro** — não importam SQLAlchemy, FastAPI nem qualquer infraestrutura (`import app.domain.entities.os` não carrega `sqlalchemy`). O mapeamento objeto-relacional vive em `app/infrastructure/orm_mapping.py` via **imperative mapping** (`registry.map_imperatively`), mantendo o domínio persistence-ignorant. Os value objects (`AcaoWebhook`, `CpfCnpj`, `Placa`) também vivem no domínio.

**Camada de aplicação:** todos os contextos (OS, cadastro, catálogo, estoque) passam por use cases; as rotas HTTP apenas traduzem entrada/saída. Use cases dependem só das portas (repositórios e `EmailNotificacaoPort`) por duck typing — sem importar SQLAlchemy nem HTTP. Ao criar uma OS, o use case dispara pela porta de saída o e-mail (simulado) de aprovação, cuja resposta retorna pelo `/webhooks/email`.

📐 **Diagramas completos (Hexagonal + Domain Storytelling + Context Map + Event Storming):**
https://excalidraw.com/#json=YiqDfj5ohxRVljjCtpOmT,h404BjQ8sBouPa8R7suTnw

---

## Infraestrutura e Fluxo de Deploy

```
  Desenvolvedor
       │
       ├─ docker compose up ──────────────────────────────────────────────┐
       │                                                                   ▼
       │                                                         [ Dev local ]
       │                                                     FastAPI :8000 + Postgres
       │
       └─ git push develop/main ──► GitHub Actions ─────────────────────────────────┐
                                                                                      │
                                  ┌───────────────────────────────────────────────────▼──┐
                                  │                  Pipeline CI/CD                       │
                                  │  job test      → pytest 101 testes + coverage         │
                                  │                → kubectl --dry-run (valida manifests) │
                                  │                                                        │
                                  │  job deploy-k8s (main) → Kind cluster                 │
                                  │    ├── kubectl apply k8s/postgres/ (StatefulSet + PVC)│
                                  │    ├── kubectl apply k8s/          (Deployment + HPA) │
                                  │    └── smoke test GET /health                         │
                                  │                                                        │
                                  │  job build-and-push (main, após deploy) → GHCR        │
                                  │    └── ghcr.io/pesant0s/tech-challenge:latest          │
                                  └────────────────────────────────────────────────────────┘
                                                         │
                                           (deploy manual minikube / Terraform)
                                                         │
                                  ┌──────────────────────▼──────────────────────────────┐
                                  │         Kubernetes cluster (minikube / cloud)        │
                                  │  namespace: oficina                                   │
                                  │                                                       │
                                  │  ┌─────────────────────┐   ┌──────────────────────┐  │
                                  │  │  Deployment API      │   │  StatefulSet Postgres│  │
                                  │  │  réplicas: 2 (→5)   │   │  PostgreSQL 16       │  │
                                  │  │  HPA CPU 70%         │   │  PVC 1Gi            │  │
                                  │  │  readinessProbe /health   └──────────┬───────────┘  │
                                  │  └────────────┬────────┘              │               │
                                  │               │ ClusterIP              │ headless svc  │
                                  │  ┌────────────▼────────┐   ┌──────────▼──────────┐  │
                                  │  │ Service NodePort     │   │ Service postgres-svc│  │
                                  │  │ :30080 → :8000      │   │ ClusterIP None:5432 │  │
                                  │  └─────────────────────┘   └─────────────────────┘  │
                                  │                                                       │
                                  │  ConfigMap: ALGORITHM, CORS   Secret: DATABASE_URL,  │
                                  │                               SECRET_KEY, WEBHOOK_SECRET│
                                  │                                                       │
                                  │  Terraform (infra/) gerencia todos os recursos acima │
                                  └───────────────────────────────────────────────────────┘
                                                         │
                                                   :30080/docs
                                                  Swagger UI
```

---

## Stack

| Componente     | Tecnologia                            |
|----------------|---------------------------------------|
| Linguagem      | Python 3.12                           |
| Framework      | FastAPI                               |
| Banco de dados | PostgreSQL 16                         |
| ORM            | SQLAlchemy 2.0                        |
| Migrations     | Alembic                               |
| Autenticação   | JWT (python-jose + bcrypt)            |
| Containers     | Docker + Docker Compose               |
| Orquestração   | Kubernetes (minikube)                 |
| IaC            | Terraform (provider kubernetes)       |
| CI/CD          | GitHub Actions + GHCR                 |
| Testes         | pytest 101 testes · SQLite in-memory  |

---

## Documentação da API (Swagger)

A documentação interativa completa está disponível em:

| Ambiente | URL |
|----------|-----|
| Local (Docker Compose) | http://localhost:8000/docs |
| Kubernetes (minikube) | `http://$(minikube ip):30080/docs` |

O Swagger inclui todos os endpoints com schemas, exemplos de payload e autenticação integrada. Clique em **Authorize 🔒**, cole o token JWT obtido em `POST /auth/token` e execute qualquer rota direto pelo navegador.

---

## Como rodar localmente (Docker Compose)

### Pré-requisitos
- Docker e Docker Compose instalados

### 1. Clonar e configurar

```bash
git clone https://github.com/pesant0s/tech-challenge
cd tech-challenge
cp .env.example .env
```

> Edite o `.env`: troque `SECRET_KEY`, `ADMIN_PASSWORD` e `WEBHOOK_SECRET` antes de qualquer uso real.

### 2. Subir (modo dev — com hot-reload)

```bash
docker compose up --build
```

### 2b. Subir (modo prod — sem volumes/reload, 2 workers)

```bash
docker compose -f docker-compose.prod.yml up --build
```

Na inicialização, o container executa automaticamente:
1. `alembic upgrade head` — aplica todas as migrations
2. Seed do usuário admin (via variáveis do `.env`)
3. Uvicorn com hot-reload (dev) ou 2 workers (prod)

### 3. Acessar

| URL                          | Descrição               |
|------------------------------|-------------------------|
| http://localhost:8000/docs   | Swagger UI (interativo) |
| http://localhost:8000/redoc  | ReDoc                   |
| http://localhost:8000/health | Health check            |

---

## Como rodar com Kubernetes (minikube)

### Pré-requisitos
- minikube e kubectl instalados

```bash
minikube start
minikube addons enable metrics-server

# Build da imagem e carga no minikube (sem registry externo)
docker build -t tech-challenge-api:latest .
minikube image load tech-challenge-api:latest

# Aplicar manifestos
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/

# Verificar
kubectl get pods -n oficina           # todos Running
kubectl get hpa -n oficina            # HPA criado

# Obter URL
minikube service tech-challenge-svc -n oficina --url
```

Acesse o Swagger na URL retornada pelo último comando.

### Estrutura `/k8s`

```
k8s/
├── namespace.yaml      # namespace: oficina
├── configmap.yaml      # variáveis não-sensíveis
├── secret.yaml         # DATABASE_URL, SECRET_KEY, WEBHOOK_SECRET (base64)
├── deployment.yaml     # 2 réplicas · readinessProbe /health · resource limits
├── service.yaml        # NodePort 30080 → 8000
├── hpa.yaml            # min 2 · max 5 · CPU 70%
└── postgres/
    ├── pvc.yaml        # PersistentVolumeClaim 1Gi
    ├── statefulset.yaml# PostgreSQL 16-alpine
    └── service.yaml    # ClusterIP postgres-svc:5432
```

---

## Como provisionar com Terraform

```bash
cd infra
terraform init
terraform plan          # mostra resources a criar sem erros
terraform apply         # aplica no minikube
terraform output        # exibe service_url
```

> Requer minikube rodando e `~/.kube/config` apontando para o contexto `minikube`.

### Estrutura `/infra`

```
infra/
├── main.tf         # provider kubernetes → minikube
├── variables.tf    # namespace, image_tag, secret_key, webhook_secret (sensitive)
├── outputs.tf      # service_url, namespace, swagger_url
├── namespace.tf    # kubernetes_namespace
├── configmap.tf    # kubernetes_config_map
├── secret.tf       # kubernetes_secret (valores das variables)
├── deployment.tf   # kubernetes_deployment (2 réplicas, probes, limits)
├── service.tf      # kubernetes_service (NodePort 30080)
└── hpa.tf          # kubernetes_horizontal_pod_autoscaler_v2
```

---

## CI/CD — GitHub Actions

Pipeline em `.github/workflows/ci.yml`:

| Job              | Trigger                     | O que faz                                     |
|------------------|-----------------------------|-----------------------------------------------|
| `test`           | push develop/main, PR→main  | pytest --cov, upload coverage.xml             |
| `build-and-push` | push main (needs: test)     | docker build + push para GHCR                 |
| `deploy-docs`    | após build-and-push         | exibe comando `kubectl set image` para deploy |

Imagem publicada em: `ghcr.io/pesant0s/tech-challenge:latest`

---

## Autenticação

O sistema usa JWT via OAuth2 Password Flow:

| Role        | Acesso                                                       |
|-------------|--------------------------------------------------------------|
| `ADMIN`     | Total — catálogo, estoque, usuários                          |
| `ATENDENTE` | Operacional — clientes, veículos, ordens de serviço          |

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

No Swagger, clique em **Authorize 🔒** e cole o token retornado.

---

## Ciclo de vida da OS

```
RECEBIDA → EM_DIAGNOSTICO → AGUARDANDO_APROVACAO → EM_EXECUCAO → FINALIZADA → ENTREGUE
                                     │
                              NEGADA / ABANDONADA
```

Ao mover para **EM_EXECUCAO**, as peças vinculadas são baixadas do estoque automaticamente.
Estoque insuficiente bloqueia a transição com erro 422.

Concorrência protegida com **SELECT FOR UPDATE** em `baixar_estoque` e `buscar_para_escrita` — evita race condition (TOCTOU) em ambientes com múltiplas réplicas.

---

## Fila de prioridade (Etapa 4)

`GET /atendimento/os/fila` — retorna OS ativas ordenadas por urgência operacional:

| Prioridade | Status               |
|-----------|----------------------|
| 1 (maior) | EM_EXECUCAO          |
| 2         | AGUARDANDO_APROVACAO |
| 3         | EM_DIAGNOSTICO       |
| 4         | RECEBIDA             |

OS com status `FINALIZADA` ou `ENTREGUE` são excluídas. Dentro de cada prioridade, a mais antiga aparece primeiro.

---

## Webhook de e-mail (Etapa 5)

`POST /webhooks/email` — permite que um serviço externo de e-mail aprove ou rejeite um orçamento:

```bash
curl -X POST http://localhost:8000/webhooks/email \
  -H "Content-Type: application/json" \
  -d '{
    "os_id": "<uuid>",
    "acao": "APROVAR",
    "cpf_cnpj": "529.982.247-25",
    "token": "webhook-secret-local"
  }'
```

| Campo      | Valores aceitos         | Descrição                              |
|------------|-------------------------|----------------------------------------|
| `acao`     | `APROVAR` ou `REJEITAR` | Enum — valores inválidos retornam 422  |
| `token`    | string                  | Deve bater com `WEBHOOK_SECRET` do `.env` |
| `cpf_cnpj` | CPF ou CNPJ             | Validado pelos dígitos verificadores   |

Token comparado com `hmac.compare_digest` (resistente a timing attacks).

---

## Variáveis de ambiente

| Variável                   | Obrigatória | Default (local)              | Descrição                                  |
|----------------------------|-------------|------------------------------|--------------------------------------------|
| `DATABASE_URL`             | ✅          | postgres://…                 | URL de conexão PostgreSQL                  |
| `SECRET_KEY`               | ✅          | —                            | Chave JWT (mínimo 32 chars)                |
| `ALGORITHM`                | ✅          | `HS256`                      | Algoritmo JWT                              |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ✅       | `60`                         | Expiração do token em minutos              |
| `ADMIN_USERNAME`           | ✅          | `admin`                      | Login do administrador                     |
| `ADMIN_PASSWORD`           | ✅          | `admin123`                   | Senha do administrador                     |
| `WEBHOOK_SECRET`           | ✅          | `webhook-secret-local`       | Token compartilhado para webhook de e-mail |
| `ALLOWED_ORIGINS`          | ✅          | `["http://localhost:3000"]`  | Lista CORS (JSON)                          |
| `POSTGRES_USER`            | ✅ (compose)| `oficina`                    | Usuário do banco                           |
| `POSTGRES_PASSWORD`        | ✅ (compose)| `oficina`                    | Senha do banco                             |
| `POSTGRES_DB`              | ✅ (compose)| `oficina`                    | Nome do banco                              |

---

## Rodar testes

Os testes usam **SQLite in-memory** — não precisam de Docker nem PostgreSQL.

```bash
# Via Docker (recomendado — ambiente idêntico ao CI)
docker compose run --rm --no-deps tech-challenge-api python -m pytest --tb=short -q

# Local
pip install -r requirements.txt
export DATABASE_URL="sqlite:///./test.db"
export SECRET_KEY="qualquer-chave-de-pelo-menos-32-caracteres"
export WEBHOOK_SECRET="webhook-secret-local"
pytest tests/ -v
```

> **Resultado esperado:** 101 testes, 0 falhas.

```bash
# Com cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Estrutura do projeto

```
app/
├── domain/                     # PURO — nenhum import de SQLAlchemy/FastAPI
│   ├── entities/           # OrdemDeServico, Cliente, Veiculo, Peca, Servico, Usuario
│   ├── value_objects/      # CpfCnpj, Placa, AcaoWebhook
│   ├── ports/              # OSRepositoryPort, EmailNotificacaoPort
│   └── exceptions.py       # Exceções Python puras (sem HTTPException)
├── application/
│   └── use_cases/          # CriarOS, AtualizarStatus, AprovarOS, RejeitarOS,
│                           # ProcessarWebhookEmail, ListarOS, GerenciarCatalogo,
│                           # GerenciarEstoque, GerenciarClientes/Veiculos
├── adapters/
│   ├── inbound/
│   │   └── http/           # *_routes.py (finos), *_schemas.py, webhook_routes.py
│   └── outbound/
│       ├── persistence/    # *_repository.py (adapters SQLAlchemy)
│       └── notifications/  # email_simulado.py (EmailNotificacaoPort)
└── infrastructure/
    ├── config.py           # Settings (pydantic-settings)
    ├── database.py         # registry + Session factory
    ├── orm_mapping.py      # Mapeamento imperativo domínio ↔ tabelas
    └── security.py         # JWT utils

k8s/                        # Manifestos Kubernetes
infra/                      # Terraform (provider kubernetes/minikube)
.github/workflows/          # CI/CD GitHub Actions
```

---

## Rotas da API

### Autenticação
| Método | Rota                   | Auth     | Descrição              |
|--------|------------------------|----------|------------------------|
| POST   | /auth/token            | Pública  | Login, retorna JWT     |
| POST   | /auth/usuarios         | ADMIN    | Criar usuário          |
| GET    | /auth/usuarios         | ADMIN    | Listar usuários        |
| DELETE | /auth/usuarios/{id}    | ADMIN    | Desativar usuário      |

### Atendimento (OS)
| Método | Rota                          | Auth      | Descrição                           |
|--------|-------------------------------|-----------|-------------------------------------|
| POST   | /atendimento/os               | ATENDENTE | Criar OS                            |
| GET    | /atendimento/os               | ATENDENTE | Listar OS (filtro por status)        |
| GET    | /atendimento/os/{id}          | Pública   | Buscar OS por ID                    |
| PATCH  | /atendimento/os/{id}/status   | ATENDENTE | Avançar status                      |
| POST   | /atendimento/os/{id}/aprovar  | Pública   | Cliente aprova orçamento            |
| POST   | /atendimento/os/{id}/rejeitar | Pública   | Cliente rejeita orçamento           |
| GET    | /atendimento/os/fila          | ATENDENTE | Fila por prioridade operacional     |
| GET    | /atendimento/os/consulta      | Pública   | OS do cliente por CPF/CNPJ          |
| GET    | /atendimento/os/tempo-medio   | ATENDENTE | Tempo médio de execução             |

### Webhook
| Método | Rota              | Auth    | Descrição                        |
|--------|-------------------|---------|----------------------------------|
| POST   | /webhooks/email   | Token   | Aprovar/rejeitar OS via e-mail   |

### Cadastro, Catálogo e Estoque
Rotas CRUD completas para clientes, veículos, serviços e peças — todas autenticadas (ADMIN ou ATENDENTE). Detalhes no Swagger: `http://localhost:8000/docs`.

---

## Segurança

- JWT com expiração configurável
- Rate limiting no login (10 req/min/IP via slowapi)
- CORS configurável via `ALLOWED_ORIGINS`
- Senhas hasheadas com bcrypt
- Webhook token validado com `hmac.compare_digest` (timing-safe)
- SELECT FOR UPDATE em operações de escrita concorrente (TOCTOU protection)
- Variáveis sensíveis via `.env` (nunca commitadas)
- Validação completa de CPF/CNPJ e placa (padrão antigo e Mercosul)
- Headers: `X-Content-Type-Options`, `X-Frame-Options`, `Server` ofuscado
