from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.modules.atendimento.models import OrdemDeServico, ItemOS, StatusOS
from app.modules.atendimento.schemas import OSCreate
from app.modules.catalogo.models import Servico
from app.modules.estoque.repository import baixar_estoque
from app.shared.exceptions import NotFoundException, BusinessRuleException

TRANSICOES_VALIDAS = {
    StatusOS.AGUARDANDO_APROVACAO: [StatusOS.RECEBIDA, StatusOS.NEGADA, StatusOS.ABANDONADA],
    StatusOS.RECEBIDA:             [StatusOS.EM_DIAGNOSTICO],
    StatusOS.EM_DIAGNOSTICO:       [StatusOS.AGUARDANDO_APROVACAO, StatusOS.EM_EXECUCAO],
    StatusOS.EM_EXECUCAO:          [StatusOS.FINALIZADA],
    StatusOS.FINALIZADA:           [StatusOS.ENTREGUE],
    StatusOS.NEGADA:               [],
    StatusOS.ENTREGUE:             [],
    StatusOS.ABANDONADA:           [],
}

def create_os(db: Session, data: OSCreate):
    from app.modules.estoque.models import Peca
    total = 0
    itens = []
    for item in data.servicos:
        s = db.query(Servico).filter(Servico.id == item.servico_id).first()
        if not s:
            raise NotFoundException(f"Serviço {item.servico_id} não encontrado")
        itens.append(ItemOS(servico_id=item.servico_id, quantidade=item.quantidade, preco_unitario=s.preco))
        total += float(s.preco) * item.quantidade
    for item in data.pecas:
        p = db.query(Peca).filter(Peca.id == item.peca_id).first()
        if not p:
            raise NotFoundException(f"Peça {item.peca_id} não encontrada")
        if p.quantidade < item.quantidade:
            raise BusinessRuleException(f"Estoque insuficiente para peça '{p.nome}'")
        itens.append(ItemOS(peca_id=item.peca_id, quantidade=item.quantidade, preco_unitario=p.preco))
        total += float(p.preco) * item.quantidade

    os = OrdemDeServico(
        cliente_id=data.cliente_id,
        veiculo_id=data.veiculo_id,
        valor_total=total,
        status=StatusOS.AGUARDANDO_APROVACAO,
    )
    db.add(os)
    db.flush()
    for item in itens:
        item.os_id = os.id
        db.add(item)
    db.commit()
    db.refresh(os)
    return os

def get_os(db: Session, os_id):
    os = db.query(OrdemDeServico).filter(OrdemDeServico.id == os_id).first()
    if not os:
        raise NotFoundException("Ordem de Serviço não encontrada")
    return os

def get_all_os(db: Session, skip: int = 0, limit: int = 100, status: StatusOS | None = None):
    q = db.query(OrdemDeServico)
    if status:
        q = q.filter(OrdemDeServico.status == status)
    return q.order_by(OrdemDeServico.criado_em.desc()).offset(skip).limit(limit).all()

def atualizar_status(db: Session, os_id, novo_status: StatusOS):
    os = get_os(db, os_id)
    permitidos = TRANSICOES_VALIDAS.get(os.status, [])
    if novo_status not in permitidos:
        raise BusinessRuleException(
            f"Transição inválida: {os.status} → {novo_status}. "
            f"Permitidos: {[s.value for s in permitidos]}"
        )
    os.status = novo_status
    if novo_status == StatusOS.EM_EXECUCAO:
        os.iniciado_em = datetime.now(timezone.utc)
        for item in os.itens:
            if item.peca_id:
                baixar_estoque(db, item.peca_id, item.quantidade, motivo=f"Baixa OS {os_id}")
    if novo_status == StatusOS.FINALIZADA:
        os.finalizado_em = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(os)
    return os

def _validar_dono_os(db: Session, os_id, cpf_cnpj: str) -> OrdemDeServico:
    """Garante que o CPF/CNPJ informado pertence ao dono da OS."""
    from app.modules.cadastro.repository import _normalizar_e_validar_cpf_cnpj
    from app.modules.cadastro.models import Cliente
    os = get_os(db, os_id)
    digits = _normalizar_e_validar_cpf_cnpj(cpf_cnpj)
    cliente = db.query(Cliente).filter(Cliente.cpf_cnpj == digits).first()
    if not cliente or os.cliente_id != cliente.id:
        raise BusinessRuleException("CPF/CNPJ não corresponde ao titular desta OS")
    return os


def aprovar_os(db: Session, os_id, cpf_cnpj: str) -> OrdemDeServico:
    os = _validar_dono_os(db, os_id, cpf_cnpj)
    if os.status != StatusOS.AGUARDANDO_APROVACAO:
        raise BusinessRuleException(
            f"OS não está aguardando aprovação (status atual: {os.status})"
        )
    return atualizar_status(db, os_id, StatusOS.RECEBIDA)


def rejeitar_os(db: Session, os_id, cpf_cnpj: str) -> OrdemDeServico:
    os = _validar_dono_os(db, os_id, cpf_cnpj)
    if os.status != StatusOS.AGUARDANDO_APROVACAO:
        raise BusinessRuleException(
            f"OS não está aguardando aprovação (status atual: {os.status})"
        )
    return atualizar_status(db, os_id, StatusOS.NEGADA)


def get_os_by_cpf_cnpj(db: Session, cpf_cnpj: str):
    from app.modules.cadastro.repository import _normalizar_e_validar_cpf_cnpj
    from app.modules.cadastro.models import Cliente
    digits = _normalizar_e_validar_cpf_cnpj(cpf_cnpj)
    cliente = db.query(Cliente).filter(Cliente.cpf_cnpj == digits).first()
    if not cliente:
        raise NotFoundException("Cliente não encontrado para o CPF/CNPJ informado")
    return (
        db.query(OrdemDeServico)
        .filter(OrdemDeServico.cliente_id == cliente.id)
        .order_by(OrdemDeServico.criado_em.desc())
        .all()
    )


def tempo_medio_execucao(db: Session):
    os_list = db.query(OrdemDeServico).filter(
        OrdemDeServico.iniciado_em.isnot(None),
        OrdemDeServico.finalizado_em.isnot(None)
    ).all()
    if not os_list:
        return {"tempo_medio_minutos": 0, "total_os_finalizadas": 0}
    total = sum((o.finalizado_em - o.iniciado_em).total_seconds() for o in os_list)
    return {
        "tempo_medio_minutos": round(total / len(os_list) / 60, 2),
        "total_os_finalizadas": len(os_list)
    }
