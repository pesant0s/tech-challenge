# Tech Challenge — Progressão e Guia de Alterações

> Documento único de acompanhamento do projeto. Atualizado a cada mudança significativa.
> Pós-Tech Software Architecture — FIAP

---

## Status das Fases

| Fase | Status | Nota |
|------|--------|------|
| Fase 01 — Monolito em camadas | ✅ Entregue e aprovada | Aprovada com feedback de melhorias |
| Fase 02 — Hexagonal + Infra | 🔄 Em andamento (9/10 etapas) | Etapas 1–9 concluídas |

---

## Fase 01

### Contexto entregue
Sistema de gestão de Ordens de Serviço para oficina mecânica. Monolito FastAPI + PostgreSQL com arquitetura em camadas seguindo DDD.

**Stack:** Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy 2.0 · Alembic · JWT · pytest

**Bounded Contexts implementados:**

| Módulo | Contexto | Subdomain |
|--------|----------|-----------|
| `auth` | IAM | Supporting |
| `atendimento` | Atendimento (OS) | Core |
| `cadastro` | Clientes e Veículos | Supporting |
| `catalogo` | Serviços | Supporting |
| `estoque` | Peças e insumos | Supporting |

**Documentação DDD:** `arquitetura.excalidraw` / https://excalidraw.com/#json=YiqDfj5ohxRVljjCtpOmT,h404BjQ8sBouPa8R7suTnw

---

### Feedback recebido

**Positivos:**
- README muito bem estruturado
- Justificativa do PostgreSQL sólida
- Event Storming cobriu bem os fluxos, linguagem ubíqua coerente com o código
- Máquina de estados da OS bem amarrada com transições validadas
- Orçamento calculado automaticamente, baixa de estoque na execução
- Validação completa de CPF/CNPJ e placa (ambos os padrões)
- JWT bem posicionado (admin protegido, consulta pública liberada)
- Relatório de vulnerabilidades com análise real do Bandit
- 91 testes cobrindo positivos, negativos, controle de acesso e fluxo completo da OS

**Pontos de melhoria (itens a corrigir):**

| # | Problema | Arquivo(s) afetado(s) | Status |
|---|----------|-----------------------|--------|
| 1 | Modelo de domínio anêmico — regras vivem no repository, não no agregado | `atendimento/models.py`, `atendimento/repository.py` | ✅ Corrigido |
| 2 | Dockerfile sem multi-stage build | `Dockerfile` | ✅ Corrigido |
| 3 | Container roda como root | `Dockerfile` | ✅ Corrigido |
| 4 | `.dockerignore` ausente | raiz do projeto | ✅ Corrigido |
| 5 | Domain Storytelling ausente na documentação | `arquitetura.excalidraw` | ✅ Corrigido |
| A | Value Objects no diagrama mas não no código (`CPF`, `CNPJ`, `Placa`) | `shared/value_objects.py`, `cadastro/schemas.py`, `cadastro/repository.py`, `atendimento/repository.py` | ✅ Corrigido |
| B | Context Map ausente na documentação DDD | `arquitetura.excalidraw` | ✅ Corrigido |
| C | `datetime.utcnow()` deprecado em `security.py` | `core/security.py` | ✅ Corrigido |

---

## Guia de Correções — Fase 01

---

### [1] Modelo de domínio menos anêmico ✅

**Problema identificado:**
Todo o comportamento da `OrdemDeServico` vivia em `repository.py`:
- `TRANSICOES_VALIDAS` — dicionário de regras de estado
- `atualizar_status()` — validava e executava transições
- `aprovar_os()` / `rejeitar_os()` — regras de aprovação pelo cliente
- Cálculo do `valor_total` disperso no `create_os()`

A entidade `OrdemDeServico` era apenas um mapeamento de colunas — sem identidade comportamental.

**Solução aplicada:**
Mover todo o comportamento para a entidade `OrdemDeServico` em `models.py`:

- `TRANSICOES_VALIDAS` → atributo de classe na entidade
- `transicionar_para(novo_status)` → valida e executa a transição, atualiza timestamps internamente
- `aprovar()` / `rejeitar()` → métodos que expressam intenção de negócio
- `ItemOS.calcular_subtotal()` → método de domínio no item
- `recalcular_total()` → método de domínio no agregado

O `repository.py` passa a ser apenas I/O: persiste, consulta e coordena efeitos colaterais cross-aggregate (ex: baixa de estoque ao entrar em `EM_EXECUCAO`).

**Arquivos alterados:**
- `app/modules/atendimento/models.py`
- `app/modules/atendimento/repository.py`

---

### [2 e 3] Dockerfile multi-stage + usuário não-root ✅

**Problema identificado:**
- Single-stage: imagem final continha pip, compiladores e outros artefatos de build
- Rodava como `root` — risco de segurança

**Solução aplicada:**
- Stage `builder`: instala dependências em `/root/.local`
- Stage `runtime`: copia apenas o resultado do build + código; cria usuário `appuser` sem privilégios
- Imagem menor e mais segura

**Arquivo alterado:** `Dockerfile`

---

### [4] .dockerignore ✅

**Problema identificado:**
Sem `.dockerignore`, o `COPY . .` enviava para o contexto do Docker: `.git`, `.venv`, `__pycache__`, arquivos de teste, `.env`, documentos e outros arquivos desnecessários.

**Efeito:** imagem maior e risco de vazar variáveis de ambiente.

**Solução:** criar `.dockerignore` na raiz excluindo tudo que não é necessário em produção.

**Arquivo criado:** `.dockerignore`

---

### [5] Domain Storytelling ✅

**O que é:**
Domain Storytelling descreve fluxos do domínio na perspectiva dos **atores** (quem faz), **objetos de trabalho** (o que é manipulado) e **atividades numeradas** (o que é feito). Complementa o Event Storming mostrando a jornada humana por trás dos eventos.

**O que foi adicionado no Excalidraw:**
3 cenários pictográficos (100 elementos novos, abaixo do Event Storming existente):

- **Cenário 1 — Atendente abre uma OS** (sentençes ①–④)
  - ① Atendente identifica Cliente (por CPF/CNPJ)
  - ② Atendente registra o Veículo do Cliente
  - ③ Atendente abre OS com Serviços / Peças
  - ④ Sistema calcula e gera Orçamento → OS

- **Cenário 2 — Cliente aprova o orçamento** (sentençes ⑤–⑦)
  - ⑤ Sistema envia Orçamento para aprovação ao Cliente
  - ⑥ Cliente aprova via CPF/CNPJ
  - ⑦ Sistema atualiza status da OS → RECEBIDA

- **Cenário 3 — Execução e entrega** (sentenças ⑧–⑪)
  - ⑧ Mecânico executa Serviços da OS
  - ⑨ Sistema baixa automaticamente o Estoque de Peças
  - ⑩ Atendente finaliza e entrega Veículo ao Cliente
  - ⑪ Sistema registra OS como ENTREGUE

**Legenda visual:**
- Caixa amarela = Ator  |  Azul = Objeto de Trabalho  |  Verde = Mudança de Estado  |  Roxo = Sistema

**Arquivo atualizado:** `arquitetura.excalidraw`

---

## Fase 02 — Em andamento

**Tema:** Qualidade, Resiliência e Escalabilidade — mesmo repositório da Fase 01.

### Decisões arquiteturais (fechadas após brainstorm)

| Decisão | Decisão tomada | Motivo |
|---------|---------------|--------|
| Estilo arquitetural | **Hexagonal pragmática** | Código já tem 60% da estrutura; sem reescrita total |
| Profundidade do refactor | **Reorganização + Ports + Use Cases** | Máximo impacto sem destruir o que funciona |
| Email webhook | **Endpoint local simulado** | Professores testam localmente; demonstra padrão sem dependência externa |
| Ambiente K8s | **minikube** | Metrics-server nativo → HPA funciona de verdade no vídeo |
| Terraform target | **Kubernetes provider (local)** | Zero custo, real IaC, demonstrável localmente |
| Registry de imagem | **GHCR** | Gratuito, autenticado com `GITHUB_TOKEN`, sem conta extra |

---

### Achados do deep search (itens adicionais ao plano original)

Durante varredura completa do código, foram identificados os seguintes pontos não previstos:

| # | Achado | Arquivo | Impacto |
|---|--------|---------|---------|
| X1 | `GET /atendimento/os/{os_id}` documentado em `main.py` como público, mas **não existe em `routes.py`** | `atendimento/routes.py` | Bug: endpoint ausente |
| X2 | `NotFoundException`, `ConflictException`, `BusinessRuleException` herdam de `HTTPException` — **domínio acoplado ao FastAPI** | `shared/exceptions.py`, `atendimento/models.py` | Violação arquitetural central do Hexagonal |
| X3 | `docker-compose.yml` tem volume `.:/app` montado sobre o container — sobrescreve `COPY . .` do Dockerfile em dev | `docker-compose.yml` | Ok para dev com hot-reload; não vai para K8s |
| X4 | Porta local do docker-compose está em `8001:8000` (mudada para evitar conflito) — professores precisam saber | `docker-compose.yml` | Documentar no README |
| X5 | Nenhum teste cobre `GET /os/{id}`, listagem com prioridade, nem webhook email | `tests/` | Novos testes necessários |

---

### Plano de execução detalhado

---

#### Etapa 1 — Corrigir acoplamento HTTP no domínio (`shared/exceptions.py`)

**O que fazer:**
- Reescrever `app/shared/exceptions.py` para exceções Python puras (sem `HTTPException`)
- Adicionar exception handlers globais em `app/main.py` para mapear cada exceção → código HTTP
- Verificar todos os arquivos que importam as exceções — nenhuma mudança de interface (só a herança muda)

**Arquivos a alterar:**
- `app/shared/exceptions.py` — remover herança de `HTTPException`
- `app/main.py` — adicionar `@app.exception_handler(NotFoundException)` etc.

**Como testar:**
- `pytest` — os 91 testes existentes devem continuar passando
- Verificar no Swagger que erros 404, 409 e 422 continuam retornando os HTTP codes corretos

**Critério de conclusão:** 91/91 testes passando + respostas HTTP idênticas às atuais.

---

#### Etapa 2 — Adicionar `GET /atendimento/os/{os_id}` (bug fix)

**O que fazer:**
- Adicionar endpoint `GET /os/{os_id}` em `atendimento/routes.py` (rota pública, sem auth)
- Usar `repo.get_os()` que já existe
- Adicionar teste `test_get_os_por_id` e `test_get_os_nao_encontrado`

**Arquivos a alterar:**
- `app/modules/atendimento/routes.py` — novo endpoint
- `tests/test_atendimento.py` — 2 novos testes

**Como testar:**
- `pytest tests/test_atendimento.py` — novos testes passando

**Critério de conclusão:** endpoint existe, responde 200 com OS e 404 quando não encontrada, sem autenticação.

---

#### Etapa 3 — Reestruturar para Arquitetura Hexagonal

**Estrutura de pastas alvo:**

```
app/
├── domain/
│   ├── entities/           # move: atendimento/models.py, cadastro/models.py, etc.
│   ├── value_objects/      # move: shared/value_objects.py
│   ├── ports/
│   │   ├── os_repository.py      # Protocol (interface)
│   │   ├── cliente_repository.py # Protocol
│   │   └── email_port.py         # Protocol para notificações
│   └── exceptions.py       # move: shared/exceptions.py (já puras após Etapa 1)
├── application/
│   └── use_cases/
│       ├── criar_os.py
│       ├── listar_os.py           # inclui a fila priorizada (Etapa 4)
│       ├── atualizar_status.py
│       ├── aprovar_os.py
│       ├── rejeitar_os.py
│       └── processar_webhook_email.py  # Etapa 5
├── adapters/
│   ├── inbound/
│   │   └── http/           # move: todos os routes.py + schemas.py
│   └── outbound/
│       └── persistence/    # move: todos os repository.py (implementam os Ports)
└── infrastructure/
    ├── database.py         # move: db/session.py + db/base.py
    ├── config.py           # move: core/config.py
    └── security.py         # move: core/security.py + core/dependencies.py
```

**O que fazer:**
- Criar a hierarquia de pastas com `__init__.py`
- Mover arquivos para novos locais (sem reescrever lógica)
- Criar Ports como `Protocol` Python para os repositórios principais
- Extrair Use Cases: uma classe por caso de uso, recebe os Ports via construtor (injeção de dependência)
- Atualizar todos os `import` nos arquivos movidos
- Atualizar `app/main.py` com novos caminhos de import

**Arquivos criados:**
- `app/domain/ports/os_repository.py`
- `app/domain/ports/email_port.py`
- `app/application/use_cases/*.py` (6 arquivos)
- Todos os `__init__.py` dos novos pacotes

**Como testar:**
- `pytest` — todos os testes devem passar sem alteração de lógica
- `uvicorn app.main:app --reload` — Swagger abre e todos os endpoints respondem

**Critério de conclusão:** testes passando + API funcionando + estrutura de pastas hexagonal visível.

---

#### Etapa 4 — Nova API: listagem de OS por prioridade

**O que fazer:**
- Adicionar endpoint `GET /atendimento/os/fila` (separado do `GET /atendimento/os` existente para não quebrar clientes)
- Ordenação: `EM_EXECUCAO=1 > AGUARDANDO_APROVACAO=2 > EM_DIAGNOSTICO=3 > RECEBIDA=4`, depois `criado_em ASC`
- Excluir status `FINALIZADA` e `ENTREGUE`
- Protegido por autenticação (operacional interno)

**Lógica SQL (SQLAlchemy):**
```python
from sqlalchemy import case
PRIORIDADE = case(
    (OrdemDeServico.status == StatusOS.EM_EXECUCAO,          1),
    (OrdemDeServico.status == StatusOS.AGUARDANDO_APROVACAO, 2),
    (OrdemDeServico.status == StatusOS.EM_DIAGNOSTICO,       3),
    (OrdemDeServico.status == StatusOS.RECEBIDA,             4),
    else_=9
)
EXCLUIDOS = [StatusOS.FINALIZADA, StatusOS.ENTREGUE]
```

**Arquivos a alterar:**
- `app/application/use_cases/listar_os.py` — lógica de fila
- `app/adapters/inbound/http/atendimento_routes.py` — novo endpoint
- `tests/test_atendimento.py` — testes de ordenação

**Novos testes:**
- `test_fila_os_ordenacao_prioridade` — cria OS em estados diferentes, verifica ordem retornada
- `test_fila_os_exclui_finalizadas` — FINALIZADA e ENTREGUE não aparecem

**Como testar:**
- `pytest tests/test_atendimento.py -k fila`
- Manualmente: criar OS em estados diferentes e verificar ordem no Swagger

**Critério de conclusão:** endpoint retorna OS na ordem correta, testes passando.

---

#### Etapa 5 — Email webhook endpoint

**O que fazer:**
- Criar endpoint `POST /webhooks/email` (sem autenticação JWT — usa token de webhook)
- Payload recebido simula o que um serviço de email enviaria:
  ```json
  {
    "os_id": "uuid",
    "acao": "APROVAR" | "REJEITAR",
    "cpf_cnpj": "529.982.247-25",
    "token": "webhook-secret-local"
  }
  ```
- Validar `token` contra `settings.WEBHOOK_SECRET` (nova variável de ambiente)
- Chamar `aprovar_os` ou `rejeitar_os` conforme `acao`
- Adicionar `WEBHOOK_SECRET` em `.env` e `.env.example`

**Arquivos a criar/alterar:**
- `app/application/use_cases/processar_webhook_email.py` — lógica do caso de uso
- `app/adapters/inbound/http/webhook_routes.py` — router novo
- `app/adapters/inbound/http/webhook_schemas.py` — schema do payload
- `app/main.py` — incluir `webhook_router`
- `app/infrastructure/config.py` — adicionar `WEBHOOK_SECRET: str`
- `.env` e `.env.example` — `WEBHOOK_SECRET=webhook-secret-local`
- `tests/test_webhook.py` — arquivo novo

**Novos testes:**
- `test_webhook_aprovar_os` — webhook aprova OS com token correto
- `test_webhook_rejeitar_os` — webhook rejeita OS com token correto
- `test_webhook_token_invalido` — retorna 403
- `test_webhook_acao_invalida` — retorna 422
- `test_webhook_os_nao_encontrada` — retorna 404
- `test_webhook_cpf_errado` — retorna 422

**Como testar:**
- `pytest tests/test_webhook.py`
- No Swagger: `POST /webhooks/email` com payload completo

**Critério de conclusão:** 6 testes passando + endpoint documentado no Swagger com exemplos.

---

#### Etapa 6 — Manifestos Kubernetes (`/k8s`)

**Arquivos a criar:**

```
k8s/
├── namespace.yaml           # namespace: oficina
├── configmap.yaml           # ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, ALLOWED_ORIGINS
├── secret.yaml              # DATABASE_URL, SECRET_KEY, WEBHOOK_SECRET (base64)
├── deployment.yaml          # app: 2 réplicas, resource limits, readinessProbe em /health
├── service.yaml             # NodePort 30080 → 8000 (para testar no minikube)
├── hpa.yaml                 # min 2, max 5, CPU 70%
└── postgres/
    ├── statefulset.yaml     # PostgreSQL 16-alpine
    ├── pvc.yaml             # PersistentVolumeClaim 1Gi
    └── service.yaml         # ClusterIP interno
```

**Como testar:**
```bash
minikube start
minikube addons enable metrics-server
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/
kubectl get pods -n oficina          # todos Running
kubectl get hpa -n oficina           # HPA criado
minikube service tech-challenge-svc -n oficina --url  # obter URL
```
Acessar Swagger na URL do minikube e executar fluxo completo.

**Critério de conclusão:** todos os pods Running, HPA criado, API acessível via `minikube service`.

---

#### Etapa 7 — Terraform (`/infra`)

**Arquivos a criar:**

```
infra/
├── main.tf          # provider kubernetes, aponta para ~/.kube/config contexto minikube
├── variables.tf     # variáveis: namespace, image_tag, webhook_secret, etc.
├── outputs.tf       # output: service_url
├── namespace.tf     # kubernetes_namespace
├── configmap.tf     # kubernetes_config_map
├── secret.tf        # kubernetes_secret
├── deployment.tf    # kubernetes_deployment
├── service.tf       # kubernetes_service
└── hpa.tf           # kubernetes_horizontal_pod_autoscaler
```

**Como testar:**
```bash
cd infra
terraform init
terraform plan      # deve mostrar resources a criar, sem erros
terraform apply     # aplica no minikube
terraform output    # mostra service_url
```

**Critério de conclusão:** `terraform apply` sem erros, estado coincide com `kubectl get all -n oficina`.

---

#### Etapa 8 — CI/CD com GitHub Actions (`.github/workflows/`)

**Arquivos a criar:**

```
.github/
└── workflows/
    └── ci.yml     # pipeline principal
```

**Pipeline `ci.yml` — jobs:**

```
on: push (develop, main) + pull_request → main

jobs:
  test:
    - checkout
    - python 3.12
    - pip install -r requirements.txt
    - pytest --cov=app --cov-report=xml
    - upload coverage artifact

  build-and-push:
    needs: test
    if: github.ref == 'refs/heads/main'
    - docker build
    - login GHCR (ghcr.io/${{ github.repository_owner }})
    - docker push ghcr.io/.../tech-challenge:${{ github.sha }}
    - docker push ghcr.io/.../tech-challenge:latest

  deploy-docs:
    needs: build-and-push
    - echo instruções de kubectl apply (sem runner conectado ao minikube local)
```

**Secrets necessários no GitHub:**
- `GHCR_TOKEN` — Personal Access Token com `write:packages`

**Como testar:**
- Push para `develop` → job `test` roda
- Merge para `main` → jobs `test` + `build-and-push` rodam
- Verificar em `ghcr.io/<usuario>/tech-challenge` que a imagem apareceu

**Critério de conclusão:** badge verde no README, imagem publicada no GHCR.

---

#### Etapa 9 — Docker revisado

**O que fazer:**
- `docker-compose.yml`: separar modo dev (com volume + reload) do modo prod (sem volume)
  - Manter `docker-compose.yml` atual como dev (com `--reload` e volume `.:/app`)
  - Criar `docker-compose.prod.yml` sem volumes e sem reload (usado nos K8s instructions do README)
- Corrigir porta de volta para `8000:8000` (ou documentar claramente que está em 8001 por conflito local)
- Verificar `.dockerignore` — está correto, sem alterações necessárias

**Arquivos a alterar/criar:**
- `docker-compose.yml` — restaurar porta 8000:8000 (professores esperam 8000)
- `docker-compose.prod.yml` — novo arquivo sem volumes e hot-reload

**Como testar:**
```bash
docker compose up --build      # deve subir na porta 8000
docker compose -f docker-compose.prod.yml up --build  # prod sem reload
```

**Critério de conclusão:** `docker compose up` sobe em 8000, API acessível em `http://localhost:8000/docs`.

---

#### Etapa 10 — README atualizado

**Seções a incluir/atualizar:**
- Arquitetura Hexagonal: diagrama de camadas em ASCII ou link para Excalidraw
- Como rodar localmente (Docker Compose)
- Como rodar com K8s + minikube (passo a passo)
- Como provisionar com Terraform
- CI/CD: badge + explicação do pipeline
- Email webhook: como testar via Swagger
- Listagem por prioridade: explicação da fila
- Variáveis de ambiente: tabela completa incluindo `WEBHOOK_SECRET`

**Critério de conclusão:** professor consegue fazer deploy do zero seguindo só o README.

---

### Estado atual do Excalidraw (`arquitetura.excalidraw`)

> Auditoria realizada em 2026-06-23 — 1.593 elementos, 891 textos.

**O que já existe no arquivo:**

| Artefato | Status |
|---|---|
| Event Storming — 3 fluxos (Criação OS, Acompanhamento, Gestão Peças) | ✅ Presente |
| Domain Storytelling — 3 cenários pictográficos (11 sentenças) | ✅ Presente |
| Context Map — relacionamentos entre Bounded Contexts | ✅ Presente |
| Modelo de Domínio — Agregados, Entidades, Value Objects por BC | ✅ Presente |
| Máquina de estados da OS com todos os status | ✅ Presente |
| Enunciado da Fase 01 embutido como quadro de referência | ✅ Presente |

**O que está FALTANDO para a Fase 02:**

| Artefato | Prioridade | Quando fazer |
|---|---|---|
| **Diagrama de Arquitetura Hexagonal** | 🔴 Crítico | Após Etapa 3 (já pode ser feito) |
| **Diagrama de Infraestrutura / Deploy** | 🔴 Crítico | Após Etapas 6-8 estarem prontas |

---

#### Diagrama de Arquitetura Hexagonal — o que deve conter

O diagrama hexagonal é o artefato de documentação mais importante da Fase 02. Sem ele, o professor não consegue validar a compreensão do padrão — o código sozinho não é suficiente.

**Estrutura a representar:**

```
┌─────────────────────────────────────────────────┐
│  INFRASTRUCTURE                                  │
│  ┌───────────────────────────────────────────┐  │
│  │  ADAPTERS                                  │  │
│  │  ┌─────────────┐   ┌─────────────────┐   │  │
│  │  │   INBOUND   │   │    OUTBOUND     │   │  │
│  │  │  HTTP/REST  │   │  SQLAlchemy     │   │  │
│  │  │  (FastAPI)  │   │  Email webhook  │   │  │
│  │  └──────┬──────┘   └──────┬──────────┘   │  │
│  │         │   APPLICATION   │              │  │
│  │         │  ┌──────────────┴──────────┐   │  │
│  │         │  │    USE CASES / PORTS    │   │  │
│  │         │  │  CriarOS  AtualizarSt.  │   │  │
│  │         │  │  AprovarOS  RejeitarOS  │   │  │
│  │         │  └──────────────┬──────────┘   │  │
│  │         │        DOMAIN   │              │  │
│  │         │  ┌──────────────┴──────────┐   │  │
│  │         └─►│  Entities  Value Obj.   │   │  │
│  │            │  OrdemDeServico  CpfCnpj│   │  │
│  │            │  Exceptions  Ports      │   │  │
│  │            └─────────────────────────┘   │  │
│  └───────────────────────────────────────────┘  │
│  config.py  database.py  security.py            │
└─────────────────────────────────────────────────┘
```

**Elementos obrigatórios no diagrama:**
- Camadas concêntricas: Domain → Application → Adapters → Infrastructure
- Inbound adapters nomeados: `atendimento_routes`, `cadastro_routes`, `auth_routes`, etc.
- Outbound adapters nomeados: `OSRepositoryAdapter`, `EstoqueRepositoryAdapter`, `ClienteRepositoryAdapter`
- Ports (interfaces Protocol): `OSRepositoryPort`, `EmailNotificacaoPort`
- Seta de dependência sempre apontando para dentro (regra da inversão)
- Os 5 Bounded Contexts mapeados à estrutura

---

#### Diagrama de Infraestrutura / Deploy — o que deve conter

**Elementos obrigatórios:**

```
GitHub Actions CI/CD Pipeline
    └── test → build → push → (instrução deploy)
              ↓
         GHCR Registry
         ghcr.io/pesant0s/tech-challenge:latest
              ↓
    ┌─── minikube (Kubernetes) ────────────────┐
    │  namespace: oficina                       │
    │                                           │
    │  Terraform (provider: kubernetes)         │
    │  ├── namespace.tf                         │
    │  ├── configmap.tf + secret.tf             │
    │  ├── deployment.tf  (2 réplicas)          │
    │  ├── service.tf     (NodePort 30080)      │
    │  ├── hpa.tf         (CPU 70%, max 5)      │
    │  └── postgres/      (StatefulSet + PVC)   │
    │                                           │
    │  Pods:                                    │
    │  ┌──────────┐  ┌──────────┐              │
    │  │ API pod  │  │ API pod  │  ← HPA       │
    │  └────┬─────┘  └────┬─────┘              │
    │       └──────┬───────┘                    │
    │         ┌────▼─────┐                      │
    │         │ postgres │ StatefulSet + PVC    │
    │         └──────────┘                      │
    └───────────────────────────────────────────┘
```

**Elementos obrigatórios no diagrama:**
- Pipeline GitHub Actions com os 3 jobs (test, build-and-push, deploy-docs)
- GHCR como registry intermediário
- minikube cluster com namespace `oficina`
- Deployment API (2 réplicas) + HPA (CPU 70%, min 2, max 5)
- Service NodePort para acesso externo (porta 30080)
- PostgreSQL StatefulSet + PersistentVolumeClaim (1Gi)
- Service ClusterIP interno para o banco
- Terraform gerenciando todos os recursos (seta de IaC)
- Seta indicando que `docker-compose.yml` é usado apenas localmente (não vai para K8s)

---

### Checklist geral — Fase 02

**Código e arquitetura:**
- [x] Etapa 1 — Exceções desacopladas do HTTP
- [x] Etapa 2 — `GET /atendimento/os/{os_id}` implementado
- [x] Etapa 3 — Reestruturação Hexagonal
- [x] Etapa 4 — Listagem de OS por prioridade (`GET /atendimento/os/fila`)
- [x] Etapa 5 — Webhook de email (`POST /webhooks/email`)

**Testes:**
- [x] 101 testes passando (base atual — cresce a cada etapa)
- [x] Testes de `GET /os/{id}` — 2 testes (Etapa 2 ✅)
- [x] Testes de fila priorizada — 2 testes (Etapa 4 ✅)
- [x] Testes de webhook email — 6 cenários (Etapa 5 ✅)

**Infraestrutura:**
- [x] Etapa 6 — Manifestos Kubernetes (`/k8s`) — 9 arquivos (namespace, configmap, secret, deployment, service, hpa, postgres/statefulset, pvc, service)
- [x] Etapa 7 — Terraform (`/infra`) — 9 arquivos (main, variables, outputs, namespace, configmap, secret, deployment, service, hpa)
- [x] Etapa 8 — GitHub Actions (`.github/workflows/ci.yml`) — jobs: test, build-and-push (main only), deploy-docs
- [x] Etapa 9 — Docker revisado — `docker-compose.prod.yml` criado, porta restaurada para 8000:8000

**Documentação (Excalidraw):**
- [x] Diagrama de Arquitetura Hexagonal — adicionado ao `arquitetura.excalidraw` (Y=26500)
- [ ] Diagrama de Infraestrutura / Deploy — fazer após Etapas 6-8

**Entregáveis finais:**
- [ ] Etapa 10 — README.md completo (incluindo referência ao Excalidraw atualizado)
- [ ] Vídeo ≤ 15 min no YouTube/Vimeo
- [ ] PDF entregue no portal

---

## Log de Alterações

| Data | O que mudou | Arquivos |
|------|------------|---------|
| 2026-06-22 | Criado PROGRESSO.md como documento unificado | `PROGRESSO.md` |
| 2026-06-22 | Modelo de domínio enriquecido: regras migradas para `OrdemDeServico` | `atendimento/models.py`, `atendimento/repository.py` |
| 2026-06-22 | Dockerfile refatorado: multi-stage + usuário não-root | `Dockerfile` |
| 2026-06-22 | Criado `.dockerignore` | `.dockerignore` |
| 2026-06-22 | Domain Storytelling adicionado: 3 cenários, 11 sentenças, 100 elementos | `arquitetura.excalidraw` |
| 2026-06-22 | Fix `datetime.utcnow()` → `datetime.now(timezone.utc)` | `core/security.py` |
| 2026-06-22 | Value Objects criados: `CpfCnpj` e `Placa` — validação consolidada em `shared/value_objects.py` | `shared/value_objects.py`, `cadastro/schemas.py`, `cadastro/repository.py`, `atendimento/repository.py` |
| 2026-06-22 | Context Map adicionado no Excalidraw | `arquitetura.excalidraw` |
| 2026-06-22 | Deep search Fase 02: achados X1–X5 documentados + plano detalhado 10 etapas | `PROGRESSO.md` |
| 2026-06-22 | Etapa 1: exceções viram Python puras; exception handlers adicionados em `main.py` — 91/91 testes ✅ | `shared/exceptions.py`, `main.py` |
| 2026-06-22 | Etapa 2: `GET /atendimento/os/{os_id}` implementado (rota pública) + 2 testes — 93/93 ✅ | `atendimento/routes.py`, `tests/test_atendimento.py` |
| 2026-06-22 | Etapa 3: Reestruturação Hexagonal completa — nova estrutura `domain/`, `application/`, `adapters/`, `infrastructure/`; Ports como Protocol; Use Cases extraídos; `modules/`, `core/`, `db/`, `shared/` removidos; `main.py`, `alembic/env.py`, `conftest.py` atualizados — 93/93 ✅ | `app/domain/`, `app/application/`, `app/adapters/`, `app/infrastructure/`, `app/main.py`, `alembic/env.py`, `tests/conftest.py` |
| 2026-06-23 | Auditoria do Excalidraw: mapeados 1.593 elementos existentes; identificados 2 diagramas obrigatórios faltantes para Fase 02 (Hexagonal + Infra/Deploy); detalhes e conteúdo de cada diagrama documentados no PROGRESSO.md | `PROGRESSO.md` |
| 2026-06-23 | Diagrama de Arquitetura Hexagonal: 1ª tentativa revertida (formato `label` do MCP incompatível com o arquivo; escala errada) — refazer com Python gerando JSON nativo | `arquitetura.excalidraw` |
| 2026-06-23 | Diagrama de Arquitetura Hexagonal adicionado corretamente: 101 elementos (38 rects + 61 texts + 2 arrows), JSON nativo Excalidraw, escala matching arquivo existente (Y=26500, fontSize 30-50). 3 colunas (Inbound/App+Domain/Outbound), Ports amarelos, Entities/VOs/Exceptions no Domain, Regra de Dependência | `arquitetura.excalidraw` |
| 2026-06-24 | Auditoria e correções Excalidraw: card BC: Autenticação adicionado ao Domain Model; nome "Catálogo" corrigido no Subdomain Map; 5 elementos lixo removidos | `arquitetura.excalidraw` |
| 2026-06-24 | Etapa 4: `GET /atendimento/os/fila` implementado (rota autenticada, prioridade EM_EXECUCAO=1 > AGUARDANDO=2 > EM_DIAGNOSTICO=3 > RECEBIDA=4, exclui FINALIZADA e ENTREGUE) + 2 testes — 95/95 ✅ | `atendimento_routes.py`, `tests/test_atendimento.py` |
| 2026-06-24 | Etapa 5: `POST /webhooks/email` implementado — token validado com `hmac.compare_digest` (timing-safe), `AcaoWebhook` enum rejeita ações inválidas, `ProcessarWebhookEmailUseCase` criado, `WEBHOOK_SECRET` em `.env` e `.env.example` — 6 testes, 101/101 ✅ | `webhook_routes.py`, `webhook_schemas.py`, `processar_webhook_email.py`, `main.py`, `.env`, `.env.example`, `tests/test_webhook.py` |
| 2026-06-24 | Excalidraw: `webhook_routes.py` card atualizado (amarelo→azul, removido "pendente"); `ProcessarWebhookEmailUseCase` adicionado no slot vazio (x=23935,y=17090) — 1712 elementos total | `arquitetura.excalidraw` |
| 2026-06-24 | Etapa 6: 9 manifestos Kubernetes criados em `/k8s` — namespace, configmap, secret, deployment (2 réplicas, readinessProbe /health), service (NodePort 30080), hpa (min2/max5/CPU70%), postgres/statefulset+pvc+service | `k8s/` |
| 2026-06-24 | Etapa 7: 9 arquivos Terraform em `/infra` — provider kubernetes/minikube, variables (sensitive), secret usando vars, hpa v2, outputs com service_url | `infra/` |
| 2026-06-24 | Etapa 8: `.github/workflows/ci.yml` — job test (SQLite, pytest --cov), build-and-push para GHCR (só main), deploy-docs com instruções kubectl | `.github/workflows/ci.yml` |
| 2026-06-24 | Etapa 9: `docker-compose.prod.yml` criado (sem volumes/reload, --workers 2); porta restaurada para 8000:8000 no `docker-compose.yml` | `docker-compose.prod.yml`, `docker-compose.yml` |
