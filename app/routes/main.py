# app/routes/main.py
from flask import Blueprint, render_template, request
from app.models import Pedido, Empresa

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/kanban')
def index():
    empresa_id = request.args.get('empresa_id', type=int)
    
    # Consulta de pedidos (geral ou filtrado por empresa)
    query = Pedido.query
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

    empresas_list = Empresa.query.all()

    # Verifica se a requisição veio via JS/AJAX (carregarTela)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(
            'dashboard/kanban.html',
            kanban=kanban_data,
            empresas_list=empresas_list,
            empresa_selecionada=empresa_id,
            total_economia="0,00",
            valor_medio="0,00"
        )

    # Se for acesso normal/F5, carrega a estrutura base com o kanban dentro
    return render_template(
        'base.html', 
        kanban=kanban_data, 
        empresas_list=empresas_list,
        empresa_selecionada=empresa_id,
        total_economia="0,00",
        valor_medio="0,00"
    )