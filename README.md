# Tech Challenge — Oficina Mecânica API

Sistema de gestão de ordens de serviço para oficinas mecânicas, desenvolvido como entrega da **Fase 1 do Tech Challenge** da Pós-Tech Software Architecture da FIAP.

---

## Objetivos

O sistema tem como objetivo digitalizar e controlar o ciclo de vida completo de uma **Ordem de Serviço (OS)** em uma oficina mecânica, cobrindo:

- Cadastro de clientes e veículos
- Abertura de OS com geração de orçamento
- Aprovação ou rejeição do orçamento pelo cliente (via CPF/CNPJ, sem autenticação)
- Diagnóstico, execução dos serviços e entrega do veículo
- Controle de estoque de peças com baixa automática ao iniciar execução
- Cálculo de métricas de tempo médio de atendimento

A arquitetura segue os princípios de **Domain-Driven Design (DDD)**, com Bounded Contexts, Linguagem Ubíqua e fluxos modelados via **Event Storming** antes da implementação.

📐 **Documentação DDD (Event Storming):** https://excalidraw.com/#json=YiqDfj5ohxRVljjCtpOmT,h404BjQ8sBouPa8R7suTnw

---

## Stack

| Componente    | Tecnologia                          |
|---------------|-------------------------------------|
| Linguagem     | Python 3.12                         |
| Framework     | FastAPI                             |
| Banco de dados| PostgreSQL 16                       |
| ORM           | SQLAlchemy 2.0                      |
| Migrations    | Alembic                             |
| Autenticação  | JWT (python-jose + bcrypt)          |
| Containers    | Docker + Docker Compose             |
| Testes        | pytest + SQLite in-memory           |

## Por que PostgreSQL?

- Transações ACID — essencial para operações de estoque sem inconsistências
- Foreign keys e constraints reforçam regras de negócio do domínio
- Suporte nativo a UUID, enums e tipos ricos usados no projeto

---

## Como rodar

### Pré-requisitos
- Docker e Docker Compose instalados

### 1. Clonar e configurar o `.env`

```bash
git clone https://github.com/pesant0s/tech-challenge
cd tech-challenge
cp .env.example .env
```

> Edite o `.env` e troque `SECRET_KEY` e `ADMIN_PASSWORD` antes de qualquer uso.

### 2. Subir os containers

```bash
docker compose up --build
```

Na inicialização, o container executa automaticamente:
1. `alembic upgrade head` — aplica todas as migrations
2. Seed do usuário admin (criado via variáveis do `.env`)
3. Uvicorn com hot-reload

### 3. Acessar a documentação

| URL                          | Descrição              |
|------------------------------|------------------------|
| http://localhost:8000/docs   | Swagger UI (interativo)|
| http://localhost:8000/redoc  | ReDoc                  |
| http://localhost:8000/health | Health check           |

---

## Autenticação e Roles

O sistema usa JWT via OAuth2 Password Flow com dois perfis de acesso:

| Role        | Acesso                                                        |
|-------------|---------------------------------------------------------------|
| `ADMIN`     | Total — gerencia usuários, catálogo de serviços e estoque     |
| `ATENDENTE` | Operacional — clientes, veículos e ordens de serviço          |

### Obter token JWT

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

No Swagger, clique em **Authorize 🔒** e cole o token retornado.

### Credenciais padrão

| Campo    | Valor padrão                              |
|----------|-------------------------------------------|
| username | `admin` (configurável em `.env`)          |
| password | `admin123` (configurável em `ADMIN_PASSWORD`) |

### Gerenciar usuários

```bash
# Criar atendente
POST /auth/usuarios   { "username": "joao", "password": "...", "role": "ATENDENTE" }

# Listar usuários
GET  /auth/usuarios

# Desativar usuário (soft delete)
DELETE /auth/usuarios/{id}
```

---

## Rotas públicas

Estas rotas não exigem autenticação — são usadas pelo cliente final:

| Rota                                       | Descrição                                          |
|--------------------------------------------|----------------------------------------------------|
| `GET /atendimento/os/consulta?cpf_cnpj=`   | Cliente consulta suas OS pelo CPF/CNPJ             |
| `POST /atendimento/os/{id}/aprovar`        | Cliente aprova o orçamento informando seu CPF/CNPJ |
| `POST /atendimento/os/{id}/rejeitar`       | Cliente rejeita o orçamento informando seu CPF/CNPJ|
| `GET /health`                              | Health check                                       |

---

## Ciclo de vida da OS

```
AGUARDANDO_APROVACAO ──► RECEBIDA ──► EM_DIAGNOSTICO ──► EM_EXECUCAO ──► FINALIZADA ──► ENTREGUE
         │
         ├──► NEGADA
         └──► ABANDONADA
```

Ao mover para **EM_EXECUCAO**, as peças vinculadas à OS são **baixadas automaticamente** do estoque. Se o saldo for insuficiente, a transição é bloqueada com erro 422.

### Criar OS

```bash
curl -X POST http://localhost:8000/atendimento/os \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": "<uuid>",
    "veiculo_id": "<uuid>",
    "servicos": [{ "servico_id": "<uuid>", "quantidade": 1 }],
    "pecas":    [{ "peca_id":   "<uuid>", "quantidade": 2 }]
  }'
```

`servicos` e `pecas` são listas independentes — ao menos uma delas deve ser preenchida.

### Avançar status da OS

```bash
curl -X PATCH http://localhost:8000/atendimento/os/{id}/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "EM_DIAGNOSTICO"}'
```

### Aprovação pelo cliente (sem token)

```bash
curl -X POST http://localhost:8000/atendimento/os/{id}/aprovar \
  -H "Content-Type: application/json" \
  -d '{"cpf_cnpj": "529.982.247-25"}'
```

---

## Estrutura do projeto

```
app/
├── core/           # Config, segurança JWT, dependências (get_current_user, require_admin)
├── db/             # Conexão e sessão do banco
├── modules/
│   ├── auth/           # Usuários, roles, autenticação
│   ├── atendimento/    # OS, orçamentos, máquina de estados
│   ├── cadastro/       # Clientes e veículos
│   ├── catalogo/       # Catálogo de serviços
│   └── estoque/        # Peças, insumos, movimentações
└── shared/         # Exceções customizadas (404, 409, 422)
```

## Bounded Contexts (DDD)

Os módulos do código espelham diretamente os Aggregates identificados no Event Storming:

| Contexto    | Módulo      | Subdomain   |
|-------------|-------------|-------------|
| IAM         | auth        | Supporting  |
| Atendimento | atendimento | Core        |
| Cadastro    | cadastro    | Supporting  |
| Catálogo    | catalogo    | Supporting  |
| Estoque     | estoque     | Supporting  |

📐 O Event Storming completo (3 fluxos: Criação de OS, Acompanhamento e Gestão de Peças) está disponível em: https://excalidraw.com/#json=YiqDfj5ohxRVljjCtpOmT,h404BjQ8sBouPa8R7suTnw

---

## Rodar testes

Os testes usam **SQLite in-memory** — não precisam de Docker nem PostgreSQL rodando.

```bash
pip install -r requirements.txt

# Variáveis necessárias (diferentes do .env de produção)
export DATABASE_URL="sqlite:///./test.db"
export SECRET_KEY="qualquer-chave-de-pelo-menos-32-caracteres"

pytest tests/ -v
```

> **Resultado esperado:** 91 testes, 0 falhas.

Para rodar com relatório de cobertura:

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Segurança

- JWT com expiração configurável via `ACCESS_TOKEN_EXPIRE_MINUTES`
- Rate limiting no endpoint de login (10 req/minuto por IP via slowapi)
- CORS configurável via `ALLOWED_ORIGINS`
- Senhas hasheadas com bcrypt 4.0.1
- Variáveis sensíveis via `.env` (nunca commitadas — ver `.gitignore`)
- Validação de CPF/CNPJ com algoritmo completo de dígitos verificadores
- Validação de placa (padrão antigo e Mercosul)
- Headers de segurança: `X-Content-Type-Options`, `X-Frame-Options`
- Header `Server` ofuscado
- CPF imutável após cadastro do cliente