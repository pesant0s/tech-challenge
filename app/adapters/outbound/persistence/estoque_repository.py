from sqlalchemy import func
from sqlalchemy.orm import Session
from app.domain.entities.estoque import Peca, MovimentacaoEstoque
from app.domain.entities.os import ItemOS
from app.domain.exceptions import NotFoundException, BusinessRuleException, ConflictException


class EstoqueRepositoryAdapter:
    """Implementação SQLAlchemy para operações de estoque."""

    def __init__(self, db: Session):
        self._db = db

    def buscar_peca(self, peca_id) -> Peca | None:
        return self._db.query(Peca).filter(Peca.id == peca_id).first()

    def buscar_peca_ou_falhar(self, peca_id) -> Peca:
        p = self.buscar_peca(peca_id)
        if not p:
            raise NotFoundException("Peça não encontrada")
        return p

    def baixar_estoque(self, peca_id, quantidade: int, motivo: str = "Baixa por OS"):
        p = self.buscar_peca_ou_falhar(peca_id)
        if p.quantidade < quantidade:
            raise BusinessRuleException(f"Estoque insuficiente para peça '{p.nome}'")
        p.quantidade -= quantidade
        mov = MovimentacaoEstoque(peca_id=peca_id, tipo="SAIDA", quantidade=quantidade, motivo=motivo)
        self._db.add(mov)
        self._db.flush()
        return p, p.quantidade < p.estoque_minimo


# Funções legadas mantidas para uso direto nas rotas de estoque

def _check_nome_unico(db: Session, nome: str, exclude_id=None):
    q = db.query(Peca).filter(func.lower(Peca.nome) == nome.strip().lower())
    if exclude_id:
        q = q.filter(Peca.id != exclude_id)
    if q.first():
        raise ConflictException("Já existe uma peça com esse nome")


def create_peca(db: Session, data):
    _check_nome_unico(db, data.nome)
    p = Peca(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def get_pecas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Peca).offset(skip).limit(limit).all()


def get_peca(db: Session, peca_id):
    p = db.query(Peca).filter(Peca.id == peca_id).first()
    if not p:
        raise NotFoundException("Peça não encontrada")
    return p


def update_peca(db: Session, peca_id, data):
    p = get_peca(db, peca_id)
    _check_nome_unico(db, data.nome, exclude_id=peca_id)
    for k, v in data.model_dump().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


def delete_peca(db: Session, peca_id):
    p = get_peca(db, peca_id)
    if db.query(ItemOS).filter(ItemOS.peca_id == peca_id).first():
        raise BusinessRuleException("Peça vinculada a OS ativa — não pode ser removida")
    db.delete(p)
    db.commit()


def registrar_entrada(db: Session, peca_id, data):
    p = get_peca(db, peca_id)
    p.quantidade += data.quantidade
    mov = MovimentacaoEstoque(peca_id=peca_id, tipo="ENTRADA", quantidade=data.quantidade, motivo=data.motivo)
    db.add(mov)
    db.commit()
    db.refresh(p)
    return p
