import enum
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, String, Numeric, ForeignKey, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.infrastructure.database import Base
from app.domain.exceptions import BusinessRuleException


class StatusOS(str, enum.Enum):
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    RECEBIDA = "RECEBIDA"
    EM_DIAGNOSTICO = "EM_DIAGNOSTICO"
    EM_EXECUCAO = "EM_EXECUCAO"
    FINALIZADA = "FINALIZADA"
    ENTREGUE = "ENTREGUE"
    NEGADA = "NEGADA"
    ABANDONADA = "ABANDONADA"


class ItemOS(Base):
    __tablename__ = "itens_os"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    os_id = Column(UUID(as_uuid=True), ForeignKey("ordens_servico.id"), nullable=False, index=True)
    servico_id = Column(UUID(as_uuid=True), ForeignKey("servicos.id"), nullable=True)
    peca_id = Column(UUID(as_uuid=True), ForeignKey("pecas.id"), nullable=True)
    quantidade = Column(Integer, nullable=False, default=1)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

    os = relationship("OrdemDeServico", back_populates="itens")

    def calcular_subtotal(self) -> Decimal:
        return Decimal(str(self.preco_unitario)) * self.quantidade


class OrdemDeServico(Base):
    __tablename__ = "ordens_servico"

    TRANSICOES_VALIDAS: dict[StatusOS, list[StatusOS]] = {
        StatusOS.AGUARDANDO_APROVACAO: [StatusOS.RECEBIDA, StatusOS.NEGADA, StatusOS.ABANDONADA],
        StatusOS.RECEBIDA:             [StatusOS.EM_DIAGNOSTICO],
        StatusOS.EM_DIAGNOSTICO:       [StatusOS.AGUARDANDO_APROVACAO, StatusOS.EM_EXECUCAO],
        StatusOS.EM_EXECUCAO:          [StatusOS.FINALIZADA],
        StatusOS.FINALIZADA:           [StatusOS.ENTREGUE],
        StatusOS.NEGADA:               [],
        StatusOS.ENTREGUE:             [],
        StatusOS.ABANDONADA:           [],
    }

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True)
    veiculo_id = Column(UUID(as_uuid=True), ForeignKey("veiculos.id"), nullable=False)
    status = Column(Enum(StatusOS), nullable=False, default=StatusOS.AGUARDANDO_APROVACAO, index=True)
    valor_total = Column(Numeric(10, 2), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    iniciado_em = Column(DateTime(timezone=True), nullable=True)
    finalizado_em = Column(DateTime(timezone=True), nullable=True)

    itens = relationship("ItemOS", back_populates="os")

    def pode_transicionar_para(self, novo_status: StatusOS) -> bool:
        return novo_status in self.TRANSICOES_VALIDAS.get(self.status, [])

    def transicionar_para(self, novo_status: StatusOS) -> None:
        if not self.pode_transicionar_para(novo_status):
            permitidos = self.TRANSICOES_VALIDAS.get(self.status, [])
            raise BusinessRuleException(
                f"Transição inválida: {self.status} → {novo_status}. "
                f"Permitidos: {[s.value for s in permitidos]}"
            )
        self.status = novo_status
        if novo_status == StatusOS.EM_EXECUCAO:
            self.iniciado_em = datetime.now(timezone.utc)
        if novo_status == StatusOS.FINALIZADA:
            self.finalizado_em = datetime.now(timezone.utc)

    def aprovar(self) -> None:
        if self.status != StatusOS.AGUARDANDO_APROVACAO:
            raise BusinessRuleException(
                f"OS não está aguardando aprovação (status atual: {self.status})"
            )
        self.transicionar_para(StatusOS.RECEBIDA)

    def rejeitar(self) -> None:
        if self.status != StatusOS.AGUARDANDO_APROVACAO:
            raise BusinessRuleException(
                f"OS não está aguardando aprovação (status atual: {self.status})"
            )
        self.transicionar_para(StatusOS.NEGADA)

    def recalcular_total(self) -> None:
        self.valor_total = sum(item.calcular_subtotal() for item in self.itens)
