import logging
from uuid import UUID

logger = logging.getLogger("oficina.notificacoes")


class EmailSimuladoAdapter:
    """Adapter de saída que SIMULA o envio de e-mail, registrando em log.

    Implementa `EmailNotificacaoPort`. Como o desafio não integra um serviço
    de e-mail real, este adapter "envia" a mensagem escrevendo no log — o
    suficiente para demonstrar o fluxo: ao criar a OS, o cliente é notificado
    para aprovar/rejeitar o orçamento (a resposta volta pelo `/webhooks/email`).

    Em produção, bastaria trocar por um adapter SMTP/SES/Mailgun **sem tocar no
    domínio nem nos use cases** — é justamente o ponto da arquitetura hexagonal.
    """

    def notificar_aprovacao_pendente(self, os_id: UUID, destinatario: str) -> None:
        logger.info(
            "📧 [E-MAIL SIMULADO] Para: %s | Assunto: Aprovação da OS %s | "
            "Corpo: Sua ordem de serviço está aguardando aprovação. "
            "Responda APROVAR ou REJEITAR pelo link do e-mail.",
            destinatario, os_id,
        )

    def notificar_status_alterado(self, os_id: UUID, novo_status: str, destinatario: str) -> None:
        logger.info(
            "📧 [E-MAIL SIMULADO] Para: %s | Assunto: Atualização da OS %s | "
            "Corpo: O status da sua ordem de serviço mudou para %s.",
            destinatario, os_id, novo_status,
        )
