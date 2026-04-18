import enum
from sqlalchemy import Column, String, Numeric, ForeignKey, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class StatusOS(str, enum.Enum):
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    RECEBIDA = "RECEBIDA"
    EM_DIAGNOSTICO = "EM_DIAGNOSTICO"
    EM_EXECUCAO = "EM_EXECUCAO"
    FINALIZADA = "FINALIZADA"
    ENTREGUE = "ENTREGUE"
    NEGADA = "NEGADA"
    ABANDONADA = "ABANDONADA"

class OrdemDeServico(Base):
    __tablename__ = "ordens_servico"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True)
    veiculo_id = Column(UUID(as_uuid=True), ForeignKey("veiculos.id"), nullable=False)
    status = Column(Enum(StatusOS), nullable=False, default=StatusOS.AGUARDANDO_APROVACAO, index=True)
    valor_total = Column(Numeric(10, 2), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    iniciado_em = Column(DateTime(timezone=True), nullable=True)
    finalizado_em = Column(DateTime(timezone=True), nullable=True)

    itens = relationship("ItemOS", back_populates="os")

class ItemOS(Base):
    __tablename__ = "itens_os"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    os_id = Column(UUID(as_uuid=True), ForeignKey("ordens_servico.id"), nullable=False, index=True)
    servico_id = Column(UUID(as_uuid=True), ForeignKey("servicos.id"), nullable=True)
    peca_id = Column(UUID(as_uuid=True), ForeignKey("pecas.id"), nullable=True)
    quantidade = Column(Integer, nullable=False, default=1)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

    os = relationship("OrdemDeServico", back_populates="itens")
