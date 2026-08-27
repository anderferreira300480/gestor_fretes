from flask import Blueprint, render_template
from app.models import Pedido

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    pedidos = Pedido.query.all()
    
    # Agrupando os pedidos por status para as colunas do Kanban
    kanban = {
        'em_cotacao': [p for p in pedidos if p.status == 'Em Cotação'],
        'aguardando_coleta': [p for p in pedidos if p.status == 'Aguardando Coleta'],
        'em_transito': [p for p in pedidos if p.status == 'Em Trânsito'],
        'entregue': [p for p in pedidos if p.status == 'Entregue'],
        'ocorrencia': [p for p in pedidos if p.status == 'Ocorrência/Sinistro'],
    }

    # Métricas de topo (KPIs)
    total_ativos = len([p for p in pedidos if p.status != 'Entregue'])
    
    return render_template('index.html', kanban=kanban, total_ativos=total_ativos)