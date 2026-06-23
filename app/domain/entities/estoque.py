from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.infrastructure.database import Base


class Peca(Base):
    __tablename__ = "pecas"
    __table_args__ = (UniqueConstraint("nome", name="uq_pecas_nome"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(150), nullable=False)
    descricao = Column(String(500), nullable=True)
    preco = Column(Numeric(10, 2), nullable=False)
    quantidade = Column(Integer, nullable=False, default=0)
    estoque_minimo = Column(Integer, nullable=False, default=1)


class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    peca_id = Column(UUID(as_uuid=True), ForeignKey("pecas.id"), nullable=False, index=True)
    tipo = Column(String(10), nullable=False)  # ENTRADA | SAIDA
    quantidade = Column(Integer, nullable=False)
    motivo = Column(String(200), nullable=True)
