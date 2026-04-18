from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_user, require_admin
from app.modules.atendimento import repository as repo
from app.modules.atendimento.models import StatusOS
from app.modules.atendimento.schemas import OSCreate, OSResponse, OSStatusUpdate, ClienteAprovacao

router = APIRouter(prefix="/atendimento", tags=["📋 Ordens de Serviço"])


@router.post("/os", response_model=OSResponse, status_code=201,
    summary="Criar Ordem de Serviço",
    description="Cria uma OS com status inicial **AGUARDANDO_APROVACAO**. O orçamento é calculado automaticamente.")
def criar_os(data: OSCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return repo.create_os(db, data)


@router.get("/os", response_model=list[OSResponse], summary="Listar todas as OS")
def listar_os(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: StatusOS | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return repo.get_all_os(db, skip=skip, limit=limit, status=status)


@router.get("/os/metricas/tempo-medio",
    summary="Tempo médio de execução",
    description="Retorna o tempo médio (em minutos) entre início e finalização. **Requer ADMIN.**")
def tempo_medio(db: Session = Depends(get_db), _=Depends(require_admin)):
    return repo.tempo_medio_execucao(db)


@router.get("/os/consulta", response_model=list[OSResponse],
    summary="Consultar OS por CPF/CNPJ (público)",
    description="Rota **pública** — o cliente informa seu CPF/CNPJ e recebe todas as suas OS com status atual.")
def consultar_os_por_cpf(cpf_cnpj: str, db: Session = Depends(get_db)):
    return repo.get_os_by_cpf_cnpj(db, cpf_cnpj)


@router.post("/os/{os_id}/aprovar", response_model=OSResponse,
    summary="Aprovar orçamento (público)",
    description="Rota **pública** — cliente aprova o orçamento informando seu CPF/CNPJ. Move a OS de `AGUARDANDO_APROVACAO` → `RECEBIDA`.")
def aprovar_os(os_id: UUID, data: ClienteAprovacao, db: Session = Depends(get_db)):
    return repo.aprovar_os(db, os_id, data.cpf_cnpj)


@router.post("/os/{os_id}/rejeitar", response_model=OSResponse,
    summary="Rejeitar orçamento (público)",
    description="Rota **pública** — cliente rejeita o orçamento informando seu CPF/CNPJ. Move a OS de `AGUARDANDO_APROVACAO` → `NEGADA`.")
def rejeitar_os(os_id: UUID, data: ClienteAprovacao, db: Session = Depends(get_db)):
    return repo.rejeitar_os(db, os_id, data.cpf_cnpj)


@router.patch("/os/{os_id}/status", response_model=OSResponse,
    summary="Atualizar status da OS",
    description="""
Transições válidas:

| De | Para |
|---|---|
| AGUARDANDO_APROVACAO | RECEBIDA, NEGADA, ABANDONADA |
| RECEBIDA | EM_DIAGNOSTICO |
| EM_DIAGNOSTICO | AGUARDANDO_APROVACAO, EM_EXECUCAO |
| EM_EXECUCAO | FINALIZADA |
| FINALIZADA | ENTREGUE |

Ao mover para **EM_EXECUCAO**, as peças vinculadas são baixadas automaticamente do estoque.
""")
def atualizar_status(
    os_id: UUID,
    data: OSStatusUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return repo.atualizar_status(db, os_id, data.status)
