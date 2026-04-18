from sqlalchemy import Column, String, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base

class Servico(Base):
    __tablename__ = "servicos"
    __table_args__ = (UniqueConstraint("nome", name="uq_servicos_nome"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(150), nullable=False)
    descricao = Column(String(500), nullable=True)
    preco = Column(Numeric(10, 2), nullable=False)
    tempo_estimado_minutos = Column(Integer, nullable=True)
