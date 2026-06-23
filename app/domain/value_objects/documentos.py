import re
from dataclasses import dataclass
from typing import Annotated
from pydantic import BeforeValidator


@dataclass(frozen=True)
class CpfCnpj:
    """Value Object: CPF (11 dígitos) ou CNPJ (14 dígitos). Armazena apenas dígitos."""

    digits: str

    def __post_init__(self):
        if not self.digits.isdigit() or len(self.digits) not in (11, 14):
            raise ValueError(f"CpfCnpj inválido: '{self.digits}'")

    @classmethod
    def from_str(cls, value: str) -> "CpfCnpj":
        if not re.match(r"^[\d.\-/]+$", value):
            raise ValueError(
                "CPF/CNPJ contém caracteres inválidos — use apenas dígitos e pontuação padrão (., -, /)"
            )
        digits = re.sub(r"\D", "", value)
        if len(digits) == 11:
            if not cls._validar_cpf(digits):
                raise ValueError("CPF inválido — dígitos verificadores incorretos")
        elif len(digits) == 14:
            if not cls._validar_cnpj(digits):
                raise ValueError("CNPJ inválido — dígitos verificadores incorretos")
        else:
            raise ValueError("CPF deve ter 11 dígitos ou CNPJ 14 dígitos")
        return cls(digits=digits)

    def __str__(self) -> str:
        return self.digits

    @property
    def tipo(self) -> str:
        return "CPF" if len(self.digits) == 11 else "CNPJ"

    @staticmethod
    def _validar_cpf(d: str) -> bool:
        if len(set(d)) == 1:
            return False
        total = sum(int(d[i]) * (10 - i) for i in range(9))
        r = total % 11
        if (0 if r < 2 else 11 - r) != int(d[9]):
            return False
        total = sum(int(d[i]) * (11 - i) for i in range(10))
        r = total % 11
        return (0 if r < 2 else 11 - r) == int(d[10])

    @staticmethod
    def _validar_cnpj(d: str) -> bool:
        if len(set(d)) == 1:
            return False
        w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        total = sum(int(d[i]) * w1[i] for i in range(12))
        r = total % 11
        if (0 if r < 2 else 11 - r) != int(d[12]):
            return False
        w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        total = sum(int(d[i]) * w2[i] for i in range(13))
        r = total % 11
        return (0 if r < 2 else 11 - r) == int(d[13])


@dataclass(frozen=True)
class Placa:
    """Value Object: placa de veículo no padrão antigo (AAA-1234) ou Mercosul (AAA1A23)."""

    valor: str

    _ANTIGO = re.compile(r"^[A-Z]{3}-\d{4}$")
    _MERCOSUL = re.compile(r"^[A-Z]{3}\d[A-Z]\d{2}$")

    @classmethod
    def from_str(cls, value: str) -> "Placa":
        v = value.upper().strip()
        if not (cls._ANTIGO.match(v) or cls._MERCOSUL.match(v)):
            raise ValueError(
                "Placa inválida. Formatos aceitos: AAA-1234 (antigo) ou AAA1A23 (Mercosul)"
            )
        return cls(valor=v)

    def __str__(self) -> str:
        return self.valor

    @property
    def formato(self) -> str:
        return "MERCOSUL" if self._MERCOSUL.match(self.valor) else "ANTIGO"


def _parse_cpf_cnpj(v: object) -> str:
    if isinstance(v, CpfCnpj):
        return v.digits
    return CpfCnpj.from_str(str(v)).digits


def _parse_placa(v: object) -> str:
    if isinstance(v, Placa):
        return v.valor
    return Placa.from_str(str(v)).valor


CpfCnpjStr = Annotated[str, BeforeValidator(_parse_cpf_cnpj)]
PlacaStr = Annotated[str, BeforeValidator(_parse_placa)]
