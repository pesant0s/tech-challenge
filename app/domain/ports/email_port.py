from typing import Protocol
from uuid import UUID


class EmailNotificacaoPort(Protocol):
    """Interface para notificação de clientes por email.

    Permite que o domínio dispare notificações sem conhecer o
    mecanismo de entrega (SMTP, Mailgun, simulação local, etc.).
    """

    def notificar_aprovacao_pendente(self, os_id: UUID, destinatario: str) -> None: ...
    def notificar_status_alterado(self, os_id: UUID, novo_status: str, destinatario: str) -> None: ...
