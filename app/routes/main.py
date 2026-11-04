"""Rotas da tela inicial e do quadro Kanban."""

from datetime import date, datetime, time, timedelta
from flask import Blueprint, render_template, request
from app.database import db
from app.models import Pedido, Empresa, Fornecedor, Transportadora, CotacaoFrete
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)


def _arquivar_entregas_expiradas():
    """Arquiva logicamente entregas confirmadas há pelo menos cinco dias."""
    agora = datetime.utcnow()
    limite = agora - timedelta(days=5)
    atualizados = Pedido.query.filter(
        Pedido.status == 'entregue',
        Pedido.data_confirmacao_entrega.isnot(None),
        Pedido.data_confirmacao_entrega <= limite,
        Pedido.arquivado_em.is_(None)
    ).update({'arquivado_em': agora}, synchronize_session=False)
    if atualizados:
        db.session.commit()


@main_bp.route('/')
@main_bp.route('/kanban')
def index():
    """Renderiza o Kanban e promove coletas vencidas para ``em_transito``."""
    empresa_id = request.args.get('empresa_id', type=int)
    _arquivar_entregas_expiradas()

    # A transição automática só acontece quando a coleta foi programada para o
    # dia atual. Se a data ainda não chegou, o pedido permanece em espera até
    # que o usuário confirme manualmente a coleta.
    pedidos_para_atualizar = Pedido.query.filter(
        Pedido.status == 'aguardando_coleta',
        Pedido.data_coleta.isnot(None),
        Pedido.data_coleta == date.today()
    ).all()
    if pedidos_para_atualizar:
        for pedido in pedidos_para_atualizar:
            pedido.status = 'em_transito'
        db.session.commit()
    
    # Consulta todos os pedidos ou apenas os vinculados à empresa escolhida.
    query = Pedido.query.filter(Pedido.arquivado_em.is_(None))
    if empresa_id:
        query = query.filter_by(empresa_id=empresa_id)
        
    pedidos = query.all()

    kanban_data = {
        'em_cotacao': [p for p in pedidos if p.status == 'em_cotacao'],
        'aguardando_coleta': [p for p in pedidos if p.status == 'aguardando_coleta'],
        'em_transito': [p for p in pedidos if p.status == 'em_transito'],
        'entregue': [p for p in pedidos if p.status == 'entregue'],
        'ocorrencia': [p for p in pedidos if p.status == 'ocorrencia']
    }

    empresas_list = Empresa.query.order_by(Empresa.razao_social).all()
    fornecedores_list = Fornecedor.query.order_by(Fornecedor.razao_social).all()
    transportadoras_list = Transportadora.query.order_by(Transportadora.razao_social).all()

    # AJAX recebe somente o fragmento; acesso direto recebe o layout completo.
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(
            'dashboard/kanban.html',
            kanban=kanban_data,
            hoje=date.today(),
            empresas_list=empresas_list,
            fornecedores_list=fornecedores_list,
            transportadoras_list=transportadoras_list,
            empresa_selecionada=empresa_id,
            total_economia="0,00",
            valor_medio="0,00"
        )

    # Se for acesso normal/F5, carrega a estrutura base com o kanban dentro
    return render_template(
        'base.html', 
        kanban=kanban_data, 
        hoje=date.today(),
        empresas_list=empresas_list,
        fornecedores_list=fornecedores_list,
        transportadoras_list=transportadoras_list,
        empresa_selecionada=empresa_id,
        total_economia="0,00",
        valor_medio="0,00"
    )


@main_bp.route('/relatorios')
def relatorios():
    """Lista pedidos arquivados com busca, período de entrega e paginação."""
    _arquivar_entregas_expiradas()

    busca = (request.args.get('busca') or '').strip()
    data_inicio_texto = (request.args.get('data_inicio') or '').strip()
    data_fim_texto = (request.args.get('data_fim') or '').strip()
    data_inicio = None
    data_fim = None
    erro_filtro = None

    try:
        data_inicio = date.fromisoformat(data_inicio_texto) if data_inicio_texto else None
        data_fim = date.fromisoformat(data_fim_texto) if data_fim_texto else None
        if data_inicio and data_fim and data_inicio > data_fim:
            erro_filtro = 'A data inicial não pode ser posterior à data final.'
    except ValueError:
        erro_filtro = 'Informe um período de datas válido.'

    query = Pedido.query.filter(Pedido.arquivado_em.isnot(None))
    if busca:
        termo = f'%{busca}%'
        query = query.filter(or_(
            Pedido.numero_pedido_compra.ilike(termo),
            Pedido.empresa.has(Empresa.razao_social.ilike(termo)),
            Pedido.fornecedor.has(Fornecedor.razao_social.ilike(termo)),
            Pedido.cotacoes.any(
                CotacaoFrete.transportadora.has(Transportadora.razao_social.ilike(termo))
            )
        ))
    if not erro_filtro and data_inicio:
        query = query.filter(
            Pedido.data_confirmacao_entrega >= datetime.combine(data_inicio, time.min)
        )
    if not erro_filtro and data_fim:
        query = query.filter(
            Pedido.data_confirmacao_entrega < datetime.combine(data_fim + timedelta(days=1), time.min)
        )

    pagina = query.order_by(
        Pedido.data_confirmacao_entrega.desc(),
        Pedido.id.desc()
    ).paginate(page=request.args.get('page', 1, type=int), per_page=25, error_out=False)

    return render_template(
        'relatorios/arquivados.html',
        tela_ativa='relatorios',
        pagina=pagina,
        busca=busca,
        data_inicio=data_inicio_texto,
        data_fim=data_fim_texto,
        erro_filtro=erro_filtro,
        filtros={'busca': busca, 'data_inicio': data_inicio_texto, 'data_fim': data_fim_texto}
    )