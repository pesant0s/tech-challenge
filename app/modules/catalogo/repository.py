from sqlalchemy import func
from sqlalchemy.orm import Session
from app.modules.catalogo.models import Servico
from app.modules.catalogo.schemas import ServicoCreate
from app.shared.exceptions import NotFoundException, BusinessRuleException, ConflictException


def _check_nome_unico(db: Session, nome: str, exclude_id=None):
    q = db.query(Servico).filter(func.lower(Servico.nome) == nome.strip().lower())
    if exclude_id:
        q = q.filter(Servico.id != exclude_id)
    if q.first():
        raise ConflictException("Já existe um serviço com esse nome")


def create_servico(db: Session, data: ServicoCreate):
    _check_nome_unico(db, data.nome)
    s = Servico(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

def get_servicos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Servico).offset(skip).limit(limit).all()

def get_servico(db: Session, servico_id):
    s = db.query(Servico).filter(Servico.id == servico_id).first()
    if not s:
        raise NotFoundException("Serviço não encontrado")
    return s

def update_servico(db: Session, servico_id, data: ServicoCreate):
    s = get_servico(db, servico_id)
    _check_nome_unico(db, data.nome, exclude_id=servico_id)
    for k, v in data.model_dump().items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s

def delete_servico(db: Session, servico_id):
    from app.modules.atendimento.models import ItemOS
    s = get_servico(db, servico_id)
    if db.query(ItemOS).filter(ItemOS.servico_id == servico_id).first():
        raise BusinessRuleException("Serviço vinculado a OS ativa — não pode ser removido")
    db.delete(s)
    db.commit()
