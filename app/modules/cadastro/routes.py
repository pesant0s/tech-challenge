from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_user, require_admin
from app.modules.cadastro import repository as repo
from app.modules.cadastro.schemas import ClienteCreate, ClienteUpdate, ClienteResponse, VeiculoCreate, VeiculoResponse
from app.shared.exceptions import NotFoundException

router = APIRouter(prefix="/cadastro", tags=["👤 Clientes e Veículos"])

@router.post("/clientes", response_model=ClienteResponse, status_code=201,
    summary="Cadastrar cliente",
    description="Cria um novo cliente. CPF (11 dígitos) ou CNPJ (14 dígitos) obrigatório e único.")
def criar_cliente(data: ClienteCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return repo.create_cliente(db, data)

@router.get("/clientes", response_model=list[ClienteResponse], summary="Listar clientes")
def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return repo.get_clientes(db, skip=skip, limit=limit)

@router.get("/clientes/buscar", response_model=ClienteResponse,
    summary="Buscar por CPF/CNPJ",
    description="Identifica cliente pelo documento. Usado no início da criação da OS.")
def buscar_cliente_por_cpf(cpf_cnpj: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    c = repo.get_cliente_by_cpf_cnpj(db, cpf_cnpj)
    if not c:
        raise NotFoundException("Cliente não encontrado")
    return c

@router.get("/clientes/{cliente_id}", response_model=ClienteResponse,
    summary="Obter cliente por ID",
    description="**Requer ADMIN.**")
def obter_cliente(cliente_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
    return repo.get_cliente(db, cliente_id)

@router.patch("/clientes/{cliente_id}", response_model=ClienteResponse,
    summary="Atualizar cliente (parcial)",
    description="Atualiza nome, e-mail e/ou telefone. **CPF/CNPJ é imutável** — incluí-lo no body retorna 422.")
def atualizar_cliente(cliente_id: UUID, data: ClienteUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return repo.update_cliente(db, cliente_id, data)

@router.post("/veiculos", response_model=VeiculoResponse, status_code=201,
    summary="Cadastrar veículo",
    description="Cadastra veículo e vincula ao cliente. Placa deve ser formato AAA-1234 ou AAA1A23 (Mercosul).")
def criar_veiculo(data: VeiculoCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return repo.create_veiculo(db, data)

@router.get("/clientes/{cliente_id}/veiculos", response_model=list[VeiculoResponse],
    summary="Listar veículos do cliente")
def listar_veiculos(cliente_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return repo.get_veiculos_by_cliente(db, cliente_id)

@router.get("/veiculos/{veiculo_id}", response_model=VeiculoResponse, summary="Obter veículo por ID")
def obter_veiculo(veiculo_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return repo.get_veiculo(db, veiculo_id)

@router.put("/veiculos/{veiculo_id}", response_model=VeiculoResponse, summary="Atualizar veículo")
def atualizar_veiculo(veiculo_id: UUID, data: VeiculoCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return repo.update_veiculo(db, veiculo_id, data)

@router.delete("/veiculos/{veiculo_id}", status_code=204, summary="Remover veículo")
def deletar_veiculo(veiculo_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    repo.delete_veiculo(db, veiculo_id)
