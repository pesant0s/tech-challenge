from app.domain.entities.os import OrdemDeServico, ItemOS, StatusOS
from app.domain.exceptions import NotFoundException, BusinessRuleException


class CriarOSUseCase:
    """Orquestra a criação de uma Ordem de Serviço com validações de domínio.

    Ao final, dispara (via porta de saída `EmailNotificacaoPort`) a notificação
    de aprovação pendente ao cliente — o e-mail cuja resposta chega depois no
    `/webhooks/email`. O notificador é injetado; o use case não conhece o meio
    de entrega (SMTP, simulação, etc.).
    """

    def __init__(self, os_repo, catalogo_repo, estoque_repo, cliente_repo=None, notificador=None):
        self._os_repo = os_repo
        self._catalogo = catalogo_repo
        self._estoque = estoque_repo
        self._cliente_repo = cliente_repo
        self._notificador = notificador

    def executar(self, cliente_id, veiculo_id, servicos, pecas) -> OrdemDeServico:
        itens = []
        for item in servicos:
            s = self._catalogo.buscar_servico(item.servico_id)
            if not s:
                raise NotFoundException(f"Serviço {item.servico_id} não encontrado")
            itens.append(ItemOS(
                servico_id=item.servico_id,
                quantidade=item.quantidade,
                preco_unitario=s.preco,
            ))
        for item in pecas:
            p = self._estoque.buscar_peca(item.peca_id)
            if not p:
                raise NotFoundException(f"Peça {item.peca_id} não encontrada")
            if p.quantidade < item.quantidade:
                raise BusinessRuleException(f"Estoque insuficiente para peça '{p.nome}'")
            itens.append(ItemOS(
                peca_id=item.peca_id,
                quantidade=item.quantidade,
                preco_unitario=p.preco,
            ))

        os = OrdemDeServico(
            cliente_id=cliente_id,
            veiculo_id=veiculo_id,
            status=StatusOS.AGUARDANDO_APROVACAO,
        )
        self._os_repo.adicionar(os)
        self._os_repo.flush()
        for item in itens:
            item.os_id = os.id
            self._os_repo.adicionar(item)
        self._os_repo.flush()
        os.recalcular_total()
        self._os_repo.commit()
        self._os_repo.refresh(os)

        self._notificar_aprovacao_pendente(os, cliente_id)
        return os

    def _notificar_aprovacao_pendente(self, os: OrdemDeServico, cliente_id) -> None:
        """Dispara o e-mail (simulado) de aprovação. Best-effort: nunca quebra a criação da OS."""
        if not self._notificador:
            return
        destinatario = "cliente"
        if self._cliente_repo:
            cliente = self._cliente_repo.buscar_por_id(cliente_id)
            if cliente:
                destinatario = cliente.email or cliente.telefone
        self._notificador.notificar_aprovacao_pendente(os.id, destinatario)
