from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models import Empresa, Fornecedor

pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')


@pedidos_bp.route('/api/empresa/<int:empresa_id>', methods=['GET'])
def obter_empresa(empresa_id):
    empresa = Empresa.query.get(empresa_id)
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404

    return jsonify({
        'endereco': empresa.endereco or '',
        'numero': empresa.numero or '',
        'bairro': empresa.bairro or '',
        'cidade': empresa.cidade or '',
        'estado': empresa.estado or '',
        'nome_contato': empresa.nome_contato or '',
        'email': empresa.email or '',
        'telefone': empresa.telefone or ''
    })


@pedidos_bp.route('/api/fornecedor/<int:fornecedor_id>', methods=['GET'])
def obter_fornecedor(fornecedor_id):
    fornecedor = Fornecedor.query.get(fornecedor_id)
    if not fornecedor:
        return jsonify({'erro': 'Fornecedor não encontrado'}), 404

    return jsonify({
        'endereco': fornecedor.endereco or '',
        'numero': fornecedor.numero or '',
        'bairro': fornecedor.bairro or '',
        'cidade': fornecedor.cidade or '',
        'estado': fornecedor.estado or '',
        'nome_contato': fornecedor.nome_contato or '',
        'email': fornecedor.email or '',
        'telefone': fornecedor.telefone or ''
    })


@pedidos_bp.route('/novo', methods=['GET'])
def novo_pedido():
    empresas = Empresa.query.all()
    fornecedores = Fornecedor.query.all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('pedidos/novo.html', empresas=empresas, fornecedores=fornecedores)
    
    return render_template('base.html', empresas=empresas, fornecedores=fornecedores, tela_ativa='novo_pedido')