from app.domain.entities.os import OrdemDeServico, StatusOS


class AtualizarStatusUseCase:
    """Valida e executa transição de status, coordenando efeitos colaterais (ex: baixa de estoque)."""

    def __init__(self, os_repo, estoque_repo):
        self._os_repo = os_repo
        self._estoque = estoque_repo

    def executar(self, os_id, novo_status: StatusOS) -> OrdemDeServico:
        os = self._os_repo.buscar_para_escrita(os_id)
        os.transicionar_para(novo_status)
        if novo_status == StatusOS.EM_EXECUCAO:
            for item in os.itens:
                if item.peca_id:
                    self._estoque.baixar_estoque(item.peca_id, item.quantidade, f"Baixa OS {os_id}")
        try:
            self._os_repo.commit()
        except Exception:
            self._os_repo.rollback()
            raise
        self._os_repo.refresh(os)
        return os
