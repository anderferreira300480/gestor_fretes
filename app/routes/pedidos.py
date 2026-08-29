from flask import Blueprint, render_template, request
from app.models import Pedido # ajuste conforme a chamada dos seus models

pedidos_bp = Blueprint('pedidos', __name__)

@pedidos_bp.route('/pedidos/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        # ... lógica para salvar o pedido ...
        return render_template('dashboard/kanban.html')
        
    return render_template('pedidos/novo.html')

@pedidos_bp.route('/pedidos/<int:id>/detalhes')
def detalhes(id):
    pedido = Pedido.query.get_or_404(id)
    return render_template('pedidos/detalhes.html', pedido=pedido)