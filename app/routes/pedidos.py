import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from app.database import db
from app.models import Empresa, Fornecedor, Pedido, CotacaoFrete, Anexo

pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'xml', 'zip', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@pedidos_bp.route('/api/empresa/<int:empresa_id>', methods=['GET'])
def obter_empresa(empresa_id):
    empresa = Empresa.query.get(empresa_id)
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404

    return jsonify({
        'cep': empresa.cep or '',
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
        'cep': fornecedor.cep or '',
        'endereco': fornecedor.endereco or '',
        'numero': fornecedor.numero or '',
        'bairro': fornecedor.bairro or '',
        'cidade': fornecedor.cidade or '',
        'estado': fornecedor.estado or '',
        'nome_contato': fornecedor.nome_contato or '',
        'email': fornecedor.email or '',
        'telefone': fornecedor.telefone or ''
    })


@pedidos_bp.route('/novo', methods=['GET', 'POST'])
def novo_pedido():
    if request.method == 'POST':
        empresa_id = request.form.get('empresa_id')
        fornecedor_id = request.form.get('fornecedor_id')
        
        # Leitura flexível dos parâmetros enviando tanto o formato 'numero_pedido' quanto 'numero_pedido_compra'
        numero_pedido_compra = request.form.get('numero_pedido_compra') or request.form.get('numero_pedido')
        valor_mercadoria = request.form.get('valor_mercadoria') or request.form.get('valor_carga') or 0.0

        novo = Pedido(
            empresa_id=empresa_id if empresa_id else None,
            fornecedor_id=fornecedor_id if fornecedor_id else None,
            numero_pedido_compra=numero_pedido_compra,
            valor_mercadoria=float(valor_mercadoria) if valor_mercadoria else 0.0,
            status='em_cotacao'
        )
        db.session.add(novo)
        db.session.commit()

        flash('Pedido salvo e movido para Em Cotação!', 'success')
        return redirect(url_for('main.index'))

    empresas = Empresa.query.all()
    fornecedores = Fornecedor.query.all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('pedidos/novo.html', empresas=empresas, fornecedores=fornecedores)
    
    return render_template('base.html', empresas=empresas, fornecedores=fornecedores, tela_ativa='novo_pedido')


# Rota explícita /salvar para compatibilidade com chamadas POST diretas
@pedidos_bp.route('/salvar', methods=['POST'])
def salvar_pedido():
    return novo_pedido()


# 1. Listar cotações em JSON para a Modal ao clicar no Card
@pedidos_bp.route('/<int:pedido_id>/cotacoes', methods=['GET'])
def listar_cotacoes(pedido_id):
    cotacoes = CotacaoFrete.query.filter_by(pedido_id=pedido_id).all()
    resultado = []
    for c in cotacoes:
        resultado.append({
            'id': c.id,
            'transportadora_nome': c.transportadora.razao_social if c.transportadora else 'Não Informado',
            'valor_frete': c.valor_frete,
            'prazo_dias': c.prazo_dias or 0,
            'aprovada': c.aprovada
        })
    return jsonify(resultado)


# 2. Incluir Cotação no Pedido
@pedidos_bp.route('/<int:pedido_id>/incluir_cotacao', methods=['POST'])
def incluir_cotacao(pedido_id):
    transportadora_id = request.form.get('transportadora_id')
    valor_frete = request.form.get('valor_frete')
    prazo_dias = request.form.get('prazo_dias')

    nova_cotacao = CotacaoFrete(
        pedido_id=pedido_id,
        transportadora_id=transportadora_id if transportadora_id else None,
        valor_frete=float(valor_frete),
        prazo_dias=int(prazo_dias) if prazo_dias else None
    )
    db.session.add(nova_cotacao)
    db.session.commit()

    flash('Cotação lançada com sucesso!', 'success')
    return redirect(url_for('main.index'))


# 3. Gerenciar Anexos (Upload e Consulta em JSON)
@pedidos_bp.route('/<int:pedido_id>/anexos', methods=['GET', 'POST'])
def gerenciar_anexos(pedido_id):
    if request.method == 'POST':
        tipo_documento = request.form.get('tipo_documento')
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo enviado', 'danger')
            return redirect(url_for('main.index'))

        file = request.files['arquivo']
        if file and allowed_file(file.filename):
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            orig_filename = secure_filename(file.filename)
            filename = f"pedido_{pedido_id}_{tipo_documento.lower().replace(' ', '_')}_{orig_filename}"
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            novo_anexo = Anexo(
                pedido_id=pedido_id,
                tipo_documento=tipo_documento,
                nome_arquivo=filename,
                caminho_arquivo=filepath
            )
            db.session.add(novo_anexo)
            db.session.commit()
            flash('Anexo armazenado com sucesso!', 'success')

        return redirect(url_for('main.index'))

    # Retorna lista de anexos em JSON
    anexos = Anexo.query.filter_by(pedido_id=pedido_id).all()
    return jsonify([{
        'id': a.id,
        'tipo_documento': a.tipo_documento,
        'nome_arquivo': a.nome_arquivo,
        'data_upload': a.data_upload.strftime('%d/%m/%Y %H:%M') if a.data_upload else ''
    } for a in anexos])


# 4. Download / Exibição de Anexos
@pedidos_bp.route('/uploads/<filename>')
def download_anexo(filename):
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    return send_from_directory(upload_folder, filename)