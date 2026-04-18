from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.modules.cadastro.routes import router as cadastro_router
from app.modules.catalogo.routes import router as catalogo_router
from app.modules.estoque.routes import router as estoque_router
from app.modules.atendimento.routes import router as atendimento_router
from app.modules.auth.routes import router as auth_router


def _seed_admin(app: FastAPI):
    from app.modules.auth.repository import get_usuario_by_username, create_usuario
    from app.modules.auth.schemas import UsuarioCreate
    from app.modules.auth.models import RoleEnum
    is_overridden = get_db in app.dependency_overrides
    db_factory = app.dependency_overrides.get(get_db, get_db)
    db = next(db_factory())
    try:
        if not get_usuario_by_username(db, settings.ADMIN_USERNAME):
            create_usuario(db, UsuarioCreate(
                username=settings.ADMIN_USERNAME,
                password=settings.ADMIN_PASSWORD,
                role=RoleEnum.ADMIN,
            ))
    finally:
        if not is_overridden:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_admin(app)
    yield


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Tech Challenge — Oficina Mecânica",
    description="""
Sistema de gestão de ordens de serviço para oficinas mecânicas.

## Autenticação

JWT via OAuth2 Password Flow (`POST /auth/token`).
Insira o token em **Authorize** → campo `Bearer`.

## Roles

| Role | Descrição |
|---|---|
| `ADMIN` | Acesso total — gerencia usuários, catálogo e estoque |
| `ATENDENTE` | Acesso operacional — clientes, veículos e ordens de serviço |

## Acesso público

| Rota | Descrição |
|---|---|
| `GET /atendimento/os/consulta?cpf_cnpj=` | Consulta de OS pelo CPF/CNPJ do cliente |
| `GET /atendimento/os/{id}` | Consulta de status da OS por ID |
| `GET /health` | Health check |

## Ciclo de vida da OS

`AGUARDANDO_APROVACAO` → `RECEBIDA` → `EM_DIAGNOSTICO` → `EM_EXECUCAO` → `FINALIZADA` → `ENTREGUE`

Transições alternativas: `NEGADA`, `ABANDONADA`
    """,
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["server"] = "webserver"
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-frame-options"] = "DENY"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cadastro_router)
app.include_router(catalogo_router)
app.include_router(estoque_router)
app.include_router(atendimento_router)


@app.post("/auth/token", tags=["Auth"], summary="Obter token JWT")
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    from app.modules.auth.repository import get_usuario_by_username
    user = get_usuario_by_username(db, form_data.username)
    if not user or not user.ativo or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "version": "1.0.0"}
