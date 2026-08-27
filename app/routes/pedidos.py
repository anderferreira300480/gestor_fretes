from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import db
from app.models import Pedido, Empresa, Transportadora

pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')

@pedidos_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        numero_pedido = request.form.get('numero_pedido_compra')
        fornecedor = request.form.get('fornecedor')
        valor_mercadoria = request.form.get('valor_mercadoria', type=float)
        peso_kg = request.form.get('peso_kg', type=float)
        empresa_id = request.form.get('empresa_id', type=int)

        novo_p = Pedido(
            numero_pedido_compra=numero_pedido,
            fornecedor=fornecedor,
            valor_mercadoria=valor_mercadoria,
            peso_kg=peso_kg,
            empresa_id=empresa_id
        )

        db.session.add(novo_p)
        db.session.commit()

        return redirect(url_for('pedidos.detalhes', id=novo_p.id))

    empresas = Empresa.query.order_by(Empresa.razao_social).all()
    return render_template('pedidos/novo.html', empresas=empresas)


@pedidos_bp.route('/<int:id>')
def detalhes(id):
    pedido = Pedido.query.get_or_404(id)
    transportadoras = Transportadora.query.order_by(Transportadora.razao_social).all()
    return render_template('pedidos/detalhes.html', pedido=pedido, transportadoras=transportadoras)