from sqlalchemy import func
from sqlalchemy.orm import Session
from app.domain.entities.catalogo import Servico
from app.domain.entities.os import ItemOS
from app.domain.exceptions import NotFoundException, BusinessRuleException, ConflictException


class CatalogoRepositoryAdapter:
    """Implementação SQLAlchemy para consultas de serviços (usada pelos use cases de OS)."""

    def __init__(self, db: Session):
        self._db = db

    def buscar_servico(self, servico_id) -> Servico | None:
        return self._db.query(Servico).filter(Servico.id == servico_id).first()


# Funções legadas para uso direto nas rotas de catálogo

def _check_nome_unico(db: Session, nome: str, exclude_id=None):
    q = db.query(Servico).filter(func.lower(Servico.nome) == nome.strip().lower())
    if exclude_id:
        q = q.filter(Servico.id != exclude_id)
    if q.first():
        raise ConflictException("Já existe um serviço com esse nome")


def create_servico(db: Session, data):
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


def update_servico(db: Session, servico_id, data):
    s = get_servico(db, servico_id)
    _check_nome_unico(db, data.nome, exclude_id=servico_id)
    for k, v in data.model_dump().items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


def delete_servico(db: Session, servico_id):
    s = get_servico(db, servico_id)
    if db.query(ItemOS).filter(ItemOS.servico_id == servico_id).first():
        raise BusinessRuleException("Serviço vinculado a OS ativa — não pode ser removido")
    db.delete(s)
    db.commit()
