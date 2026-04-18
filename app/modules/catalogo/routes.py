from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_user, require_admin
from app.modules.catalogo import repository as repo
from app.modules.catalogo.schemas import ServicoCreate, ServicoResponse

router = APIRouter(prefix="/catalogo", tags=["🔧 Catálogo de Serviços"])


@router.post("/servicos", response_model=ServicoResponse, status_code=201,
    summary="Criar serviço",
    description="**Requer ADMIN.**")
def criar_servico(data: ServicoCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return repo.create_servico(db, data)


@router.get("/servicos", response_model=list[ServicoResponse], summary="Listar serviços")
def listar_servicos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return repo.get_servicos(db, skip=skip, limit=limit)


@router.get("/servicos/{servico_id}", response_model=ServicoResponse, summary="Obter serviço")
def obter_servico(servico_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return repo.get_servico(db, servico_id)


@router.put("/servicos/{servico_id}", response_model=ServicoResponse,
    summary="Atualizar serviço",
    description="**Requer ADMIN.**")
def atualizar_servico(servico_id: UUID, data: ServicoCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return repo.update_servico(db, servico_id, data)


@router.delete("/servicos/{servico_id}", status_code=204,
    summary="Remover serviço",
    description="Não permite remoção se o serviço estiver vinculado a uma OS. **Requer ADMIN.**")
def deletar_servico(servico_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    repo.delete_servico(db, servico_id)
