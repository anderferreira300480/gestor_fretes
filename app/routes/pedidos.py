from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import db
from app.models import Pedido, Empresa, Fornecedor, Transportadora

pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')

@pedidos_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        numero_pedido = request.form.get('numero_pedido_compra')
        empresa_id = request.form.get('empresa_id')
        fornecedor_id = request.form.get('fornecedor_id')
        valor = request.form.get('valor_mercadoria')
        peso = request.form.get('peso_kg')

        # Dados manuais de contato da Empresa Compradora
        empresa_contato_nome = request.form.get('empresa_contato_nome')
        empresa_contato_email = request.form.get('empresa_contato_email')
        empresa_contato_telefone = request.form.get('empresa_contato_telefone')

        novo_pedido = Pedido(
            numero_pedido_compra=numero_pedido,
            empresa_id=empresa_id,
            fornecedor_id=fornecedor_id,
            valor_mercadoria=float(valor) if valor else 0.0,
            peso_kg=float(peso) if peso else 0.0,
            empresa_contato_nome=empresa_contato_nome,
            empresa_contato_email=empresa_contato_email,
            empresa_contato_telefone=empresa_contato_telefone,
            status='Em Cotação'
        )

        db.session.add(novo_pedido)
        db.session.commit()
        return redirect(url_for('main.index'))

    empresas = Empresa.query.order_by(Empresa.razao_social).all()
    fornecedores = Fornecedor.query.order_by(Fornecedor.razao_social).all()
    
    return render_template('pedidos/novo.html', empresas=empresas, fornecedores=fornecedores)