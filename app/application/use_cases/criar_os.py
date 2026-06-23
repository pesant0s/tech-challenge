from sqlalchemy.orm import Session
from app.domain.entities.os import OrdemDeServico, ItemOS, StatusOS
from app.domain.entities.catalogo import Servico
from app.domain.entities.estoque import Peca
from app.domain.exceptions import NotFoundException, BusinessRuleException


class CriarOSUseCase:
    """Orquestra a criação de uma Ordem de Serviço com validações de domínio."""

    def __init__(self, db: Session, catalogo_repo, estoque_repo):
        self._db = db
        self._catalogo = catalogo_repo
        self._estoque = estoque_repo

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
        self._db.add(os)
        self._db.flush()
        for item in itens:
            item.os_id = os.id
            self._db.add(item)
        self._db.flush()
        os.recalcular_total()
        self._db.commit()
        self._db.refresh(os)
        return os
