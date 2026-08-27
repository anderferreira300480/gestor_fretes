from flask import Blueprint, request, redirect, url_for
from app.database import db
from app.models import CotacaoFrete, Pedido

cotacoes_bp = Blueprint('cotacoes', __name__, url_prefix='/cotacoes')

@cotacoes_bp.route('/adicionar/<int:pedido_id>', methods=['POST'])
def adicionar(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)

    nova_cotacao = CotacaoFrete(
        pedido_id=pedido.id,
        transportadora_id=request.form.get('transportadora_id', type=int),
        valor_cotado=request.form.get('valor_cotado', type=float),
        prazo_dias=request.form.get('prazo_dias', type=int),
        observacoes=request.form.get('observacoes')
    )

    db.session.add(nova_cotacao)
    db.session.commit()

    return redirect(url_for('pedidos.detalhes', id=pedido.id))