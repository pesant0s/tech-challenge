from sqlalchemy.orm import Session
from app.domain.entities.cliente import Cliente, Veiculo
from app.domain.exceptions import NotFoundException, ConflictException, BusinessRuleException
from app.domain.value_objects.documentos import CpfCnpj


class ClienteRepositoryAdapter:
    """Implementação SQLAlchemy para consultas de clientes (usada pelos use cases de OS)."""

    def __init__(self, db: Session):
        self._db = db

    def buscar_por_cpf_cnpj_digits(self, digits: str) -> Cliente | None:
        return self._db.query(Cliente).filter(Cliente.cpf_cnpj == digits).first()


# Funções legadas para uso direto nas rotas de cadastro

def get_cliente_by_cpf_cnpj(db: Session, cpf_cnpj: str):
    try:
        digits = CpfCnpj.from_str(cpf_cnpj).digits
    except ValueError as exc:
        raise BusinessRuleException(str(exc))
    return db.query(Cliente).filter(Cliente.cpf_cnpj == digits).first()


def create_cliente(db: Session, data):
    if get_cliente_by_cpf_cnpj(db, data.cpf_cnpj):
        raise ConflictException("CPF/CNPJ já cadastrado")
    cliente = Cliente(**data.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def get_clientes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Cliente).offset(skip).limit(limit).all()


def get_cliente(db: Session, cliente_id):
    c = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not c:
        raise NotFoundException("Cliente não encontrado")
    return c


def update_cliente(db: Session, cliente_id, data):
    c = get_cliente(db, cliente_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


def create_veiculo(db: Session, data):
    get_cliente(db, data.cliente_id)
    if db.query(Veiculo).filter(Veiculo.placa == data.placa).first():
        raise ConflictException("Placa já cadastrada")
    v = Veiculo(**data.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def get_veiculos_by_cliente(db: Session, cliente_id):
    get_cliente(db, cliente_id)
    return db.query(Veiculo).filter(Veiculo.cliente_id == cliente_id).all()


def get_veiculo(db: Session, veiculo_id):
    v = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()
    if not v:
        raise NotFoundException("Veículo não encontrado")
    return v


def update_veiculo(db: Session, veiculo_id, data):
    v = get_veiculo(db, veiculo_id)
    for k, val in data.model_dump().items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    return v


def delete_veiculo(db: Session, veiculo_id):
    v = get_veiculo(db, veiculo_id)
    db.delete(v)
    db.commit()
