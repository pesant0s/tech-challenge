# Tech Challenge — Oficina Mecânica API

Sistema de gestão de ordens de serviço para oficinas mecânicas, desenvolvido com arquitetura monolítica em camadas seguindo princípios de DDD.

## Stack

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Framework | FastAPI |
| Banco de dados | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Autenticação | JWT (python-jose + bcrypt) |
| Containers | Docker + Docker Compose |
| Testes | pytest + SQLite in-memory |

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
git clone <repo>
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

| URL | Descrição |
|---|---|
| http://localhost:8000/docs | Swagger UI (interativo) |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/health | Health check |

---

## Autenticação e Roles

O sistema usa JWT via OAuth2 Password Flow com dois perfis de acesso:

| Role | Acesso |
|---|---|
| `ADMIN` | Total — gerencia usuários, catálogo de serviços e estoque |
| `ATENDENTE` | Operacional — clientes, veículos e ordens de serviço |

### Obter token JWT

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

No Swagger, clique em **Authorize 🔒** e cole o token retornado.

### Credenciais padrão

| Campo | Valor padrão |
|---|---|
| username | `admin` (configurável em `ADMIN_USERNAME`) |
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

| Rota | Descrição |
|---|---|
| `GET /atendimento/os/consulta?cpf_cnpj=` | Cliente consulta suas OS pelo CPF/CNPJ |
| `POST /atendimento/os/{id}/aprovar` | Cliente aprova o orçamento informando seu CPF/CNPJ |
| `POST /atendimento/os/{id}/rejeitar` | Cliente rejeita o orçamento informando seu CPF/CNPJ |
| `GET /health` | Health check |

---

## Ciclo de vida da OS

```
AGUARDANDO_APROVACAO ──► RECEBIDA ──► EM_DIAGNOSTICO ──► EM_EXECUCAO ──► FINALIZADA ──► ENTREGUE
         │
         ├──► NEGADA
         └──► ABANDONADA
```

Ao mover para **EM_EXECUCAO**, as peças vinculadas à OS são **baixadas automaticamente** do estoque.

### Criar OS

```json
POST /atendimento/os
{
  "cliente_id": "...",
  "veiculo_id": "...",
  "servicos": [
    { "servico_id": "...", "quantidade": 1 }
  ],
  "pecas": [
    { "peca_id": "...", "quantidade": 2 }
  ]
}
```

`servicos` e `pecas` são listas independentes — ao menos uma delas deve ser preenchida.

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

| Contexto | Módulo | Subdomain |
|---|---|---|
| IAM | auth | Supporting |
| Atendimento | atendimento | Core |
| Cadastro | cadastro | Supporting |
| Catálogo | catalogo | Supporting |
| Estoque | estoque | Supporting |

---

## Rodar testes

Os testes usam SQLite in-memory — não precisam de Docker nem PostgreSQL.

```bash
pip install -r requirements.txt
pytest tests/ -v
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Segurança

- JWT com expiração configurável via `ACCESS_TOKEN_EXPIRE_MINUTES`
- Rate limiting no endpoint de login (10 req/minuto por IP)
- CORS configurável via `ALLOWED_ORIGINS`
- Senhas hasheadas com bcrypt
- Variáveis sensíveis via `.env` (nunca commitadas)
- Validação de CPF/CNPJ com dígitos verificadores
- Validação de placa (padrão antigo e Mercosul)
- Headers de segurança: `X-Content-Type-Options`, `X-Frame-Options`
- Header `Server` ofuscado
