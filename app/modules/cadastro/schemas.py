import re
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, EmailStr


def _validate_cpf(digits: str) -> bool:
    if len(set(digits)) == 1:
        return False
    weights = list(range(10, 1, -1))
    total = sum(int(d) * w for d, w in zip(digits[:9], weights))
    r = total % 11
    first = 0 if r < 2 else 11 - r
    if first != int(digits[9]):
        return False
    weights = list(range(11, 1, -1))
    total = sum(int(d) * w for d, w in zip(digits[:10], weights))
    r = total % 11
    second = 0 if r < 2 else 11 - r
    return second == int(digits[10])


def _validate_cnpj(digits: str) -> bool:
    if len(set(digits)) == 1:
        return False
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(digits[:12], weights1))
    r = total % 11
    first = 0 if r < 2 else 11 - r
    if first != int(digits[12]):
        return False
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(digits[:13], weights2))
    r = total % 11
    second = 0 if r < 2 else 11 - r
    return second == int(digits[13])


def _normalizar_cpf_cnpj(v: str) -> str:
    """Aceita somente dígitos e pontuação padrão de CPF/CNPJ. Retorna apenas dígitos."""
    if not re.match(r"^[\d.\-/]+$", v):
        raise ValueError(
            "CPF/CNPJ contém caracteres inválidos — use apenas dígitos e pontuação padrão (., -, /)"
        )
    return re.sub(r"\D", "", v)


def _normalizar_telefone(v: str) -> str:
    """Aceita dígitos e pontuação telefônica padrão. Retorna apenas dígitos."""
    if not re.match(r"^[\d\s()\-+]+$", v):
        raise ValueError("Telefone contém caracteres inválidos")
    return re.sub(r"\D", "", v)


class ClienteCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    cpf_cnpj: str
    email: EmailStr | None = None
    telefone: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nome": "João Silva",
                    "cpf_cnpj": "529.982.247-25",
                    "email": "joao@email.com",
                    "telefone": "(11) 99999-9999",
                }
            ]
        }
    }

    @field_validator("cpf_cnpj")
    @classmethod
    def validate_cpf_cnpj(cls, v: str) -> str:
        digits = _normalizar_cpf_cnpj(v)
        if len(digits) == 11:
            if not _validate_cpf(digits):
                raise ValueError("CPF inválido — dígitos verificadores incorretos")
        elif len(digits) == 14:
            if not _validate_cnpj(digits):
                raise ValueError("CNPJ inválido — dígitos verificadores incorretos")
        else:
            raise ValueError("CPF deve ter 11 dígitos ou CNPJ 14 dígitos")
        return digits  # armazena apenas dígitos

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, v: str) -> str:
        digits = _normalizar_telefone(v)
        if not (10 <= len(digits) <= 11):
            raise ValueError("Telefone inválido — informe DDD + número (10 ou 11 dígitos)")
        return digits  # armazena apenas dígitos


class ClienteUpdate(BaseModel):
    """Atualização parcial de cliente — CPF/CNPJ é imutável e não pode ser enviado."""

    nome: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    telefone: str | None = None

    @model_validator(mode="before")
    @classmethod
    def rejeitar_cpf_cnpj(cls, data):
        if isinstance(data, dict) and "cpf_cnpj" in data:
            raise ValueError("CPF/CNPJ não pode ser alterado após o cadastro")
        return data

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = _normalizar_telefone(v)
        if not (10 <= len(digits) <= 11):
            raise ValueError("Telefone inválido — informe DDD + número (10 ou 11 dígitos)")
        return digits


class ClienteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome: str
    cpf_cnpj: str
    email: str | None = None
    telefone: str


class VeiculoCreate(BaseModel):
    placa: str
    marca: str = Field(min_length=1, max_length=100)
    modelo: str = Field(min_length=1, max_length=100)
    ano: str
    cliente_id: UUID

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "placa": "ABC-1234",
                    "marca": "Toyota",
                    "modelo": "Corolla",
                    "ano": "2022",
                    "cliente_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                }
            ]
        }
    }

    @field_validator("placa")
    @classmethod
    def validate_placa(cls, v: str) -> str:
        v = v.upper().strip()
        if not (re.match(r"^[A-Z]{3}-\d{4}$", v) or re.match(r"^[A-Z]{3}\d[A-Z]\d{2}$", v)):
            raise ValueError("Placa inválida. Formatos aceitos: AAA-1234 (antigo) ou AAA1A23 (Mercosul)")
        return v

    @field_validator("ano")
    @classmethod
    def validate_ano(cls, v: str) -> str:
        if not re.match(r"^\d{4}$", v) or not (1900 <= int(v) <= 2100):
            raise ValueError("Ano inválido")
        return v


class VeiculoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    placa: str
    marca: str
    modelo: str
    ano: str
    cliente_id: UUID
