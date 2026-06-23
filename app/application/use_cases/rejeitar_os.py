from sqlalchemy.orm import Session
from app.domain.entities.os import OrdemDeServico
from app.domain.exceptions import BusinessRuleException
from app.domain.value_objects.documentos import CpfCnpj


class RejeitarOSUseCase:
    """Cliente rejeita o orçamento informando seu CPF/CNPJ."""

    def __init__(self, db: Session, os_repo, cliente_repo):
        self._db = db
        self._os_repo = os_repo
        self._cliente_repo = cliente_repo

    def executar(self, os_id, cpf_cnpj: str) -> OrdemDeServico:
        try:
            digits = CpfCnpj.from_str(cpf_cnpj).digits
        except ValueError as exc:
            raise BusinessRuleException(str(exc))

        os = self._os_repo.buscar_ou_falhar(os_id)
        cliente = self._cliente_repo.buscar_por_cpf_cnpj_digits(digits)
        if not cliente or os.cliente_id != cliente.id:
            raise BusinessRuleException("CPF/CNPJ não corresponde ao titular desta OS")

        os.rejeitar()
        self._db.commit()
        self._db.refresh(os)
        return os
