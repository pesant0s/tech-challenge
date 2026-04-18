from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(150), nullable=False)
    cpf_cnpj = Column(String(18), nullable=False, unique=True)
    email = Column(String(150), nullable=True)
    telefone = Column(String(20), nullable=False)

    veiculos = relationship("Veiculo", back_populates="cliente")

class Veiculo(Base):
    __tablename__ = "veiculos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placa = Column(String(10), nullable=False, unique=True)
    marca = Column(String(60), nullable=False)
    modelo = Column(String(60), nullable=False)
    ano = Column(String(4), nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True)

    cliente = relationship("Cliente", back_populates="veiculos")
