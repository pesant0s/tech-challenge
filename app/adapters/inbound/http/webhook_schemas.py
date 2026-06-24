from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


class AcaoWebhook(str, Enum):
    APROVAR = "APROVAR"
    REJEITAR = "REJEITAR"


class WebhookEmailPayload(BaseModel):
    os_id: UUID
    acao: AcaoWebhook
    cpf_cnpj: str = Field(min_length=11, max_length=18)
    token: str = Field(min_length=1)
