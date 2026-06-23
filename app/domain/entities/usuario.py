import enum
import uuid
from sqlalchemy import Boolean, Column, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from app.infrastructure.database import Base


class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    ATENDENTE = "ATENDENTE"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.ATENDENTE)
    ativo = Column(Boolean, nullable=False, default=True)
