from sqlalchemy.orm import Session
from app.domain.entities.os import OrdemDeServico
from app.adapters.inbound.http.webhook_schemas import AcaoWebhook
from app.application.use_cases.aprovar_os import AprovarOSUseCase
from app.application.use_cases.rejeitar_os import RejeitarOSUseCase


class ProcessarWebhookEmailUseCase:
    """Processa a resposta do cliente recebida via link de e-mail."""

    def __init__(self, db: Session, os_repo, cliente_repo):
        self._db = db
        self._os_repo = os_repo
        self._cliente_repo = cliente_repo

    def executar(self, os_id, acao: AcaoWebhook, cpf_cnpj: str) -> OrdemDeServico:
        if acao == AcaoWebhook.APROVAR:
            return AprovarOSUseCase(
                db=self._db,
                os_repo=self._os_repo,
                cliente_repo=self._cliente_repo,
            ).executar(os_id, cpf_cnpj)
        return RejeitarOSUseCase(
            db=self._db,
            os_repo=self._os_repo,
            cliente_repo=self._cliente_repo,
        ).executar(os_id, cpf_cnpj)
