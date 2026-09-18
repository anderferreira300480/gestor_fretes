import os
from datetime import datetime
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
        
        numero_pedido_compra = request.form.get('numero_pedido_compra') or request.form.get('numero_pedido')
        valor_mercadoria = request.form.get('valor_mercadoria') or request.form.get('valor_carga') or 0.0

        def converter_float(nome):
            valor = request.form.get(nome)
            return float(valor) if valor else None

        novo = Pedido(
            empresa_id=empresa_id if empresa_id else None,
            fornecedor_id=fornecedor_id if fornecedor_id else None,
            numero_pedido_compra=numero_pedido_compra,
            valor_mercadoria=float(valor_mercadoria) if valor_mercadoria else 0.0,
            volumes=int(request.form['volumes']) if request.form.get('volumes') else None,
            peso_kg=converter_float('peso_kg'),
            dim_altura=converter_float('dim_altura'),
            dim_largura=converter_float('dim_largura'),
            dim_comprimento=converter_float('dim_comprimento'),
            observacoes=request.form.get('observacoes') or None,
            status='em_cotacao'
        )
        db.session.add(novo)
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({
                'sucesso': True,
                'mensagem': 'Pedido salvo e movido para Em Cotação!',
                'pedido_id': novo.id
            })

        flash('Pedido salvo e movido para Em Cotação!', 'success')
        return redirect(url_for('main.index'))

    empresas = Empresa.query.all()
    fornecedores = Fornecedor.query.all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('pedidos/novo.html', empresas=empresas, fornecedores=fornecedores)
    
    return render_template('base.html', empresas=empresas, fornecedores=fornecedores, tela_ativa='novo_pedido')


@pedidos_bp.route('/salvar', methods=['POST'])
def salvar_pedido():
    return novo_pedido()


@pedidos_bp.route('/<int:pedido_id>/excluir', methods=['POST'])
def excluir_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    db.session.delete(pedido)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'sucesso': True, 'mensagem': 'Pedido excluído com sucesso.'})

    flash('Pedido excluído com sucesso.', 'success')
    return redirect(url_for('main.index'))


# 1. Listar cotações em JSON para a Modal ao clicar no Card (inclui o status do pedido para desabilitar o form)
@pedidos_bp.route('/<int:pedido_id>/cotacoes', methods=['GET'])
def listar_cotacoes(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    cotacoes = CotacaoFrete.query.filter_by(pedido_id=pedido_id).all()
    
    resultado_cotacoes = []
    for c in cotacoes:
        resultado_cotacoes.append({
            'id': c.id,
            'transportadora_nome': c.transportadora.razao_social if c.transportadora else 'Não Informado',
            'valor_frete': c.valor_frete,
            'prazo_dias': c.prazo_dias or 0,
            'aprovada': c.aprovada,
            'observacao': c.observacao or ''
        })

    return jsonify({
        'pedido_id': pedido.id,
        'numero_pedido_compra': pedido.numero_pedido_compra,
        'valor_mercadoria': pedido.valor_mercadoria or 0,
        'volumes': pedido.volumes,
        'peso_kg': pedido.peso_kg,
        'dim_altura': pedido.dim_altura,
        'dim_largura': pedido.dim_largura,
        'dim_comprimento': pedido.dim_comprimento,
        'observacoes': pedido.observacoes or '',
        'pedido_status': pedido.status,
        'empresa': {
            'razao_social': pedido.empresa.razao_social if pedido.empresa else '',
            'cnpj': pedido.empresa.cnpj if pedido.empresa else ''
        },
        'fornecedor': {
            'razao_social': pedido.fornecedor.razao_social if pedido.fornecedor else '',
            'cnpj': pedido.fornecedor.cnpj if pedido.fornecedor else ''
        },
        'data_coleta': pedido.data_coleta.isoformat() if pedido.data_coleta else '',
        'data_entrega': pedido.data_entrega.isoformat() if pedido.data_entrega else '',
        'cotacoes_encerradas': pedido.status != 'em_cotacao',
        'cotacoes_count': len(cotacoes),
        'cotacoes': resultado_cotacoes
    })


# 2. Incluir Cotação no Pedido (com trava se o pedido já saiu da fase 'em_cotacao')
@pedidos_bp.route('/<int:pedido_id>/incluir_cotacao', methods=['POST'])
def incluir_cotacao(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    
    if pedido.status != 'em_cotacao':
        flash('Não é possível adicionar novas cotações para este pedido pois a cotação já foi encerrada.', 'warning')
        return redirect(url_for('main.index'))

    transportadora_id = request.form.get('transportadora_id')
    valor_frete = request.form.get('valor_frete')
    prazo_dias = request.form.get('prazo_dias')

    nova_cotacao = CotacaoFrete(
        pedido_id=pedido_id,
        transportadora_id=transportadora_id if transportadora_id else None,
        valor_frete=float(valor_frete),
        prazo_dias=int(prazo_dias) if prazo_dias else None,
        aprovada=False
    )
    db.session.add(nova_cotacao)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'sucesso': True,
            'pedido_id': pedido.id,
            'cotacoes_count': CotacaoFrete.query.filter_by(pedido_id=pedido.id).count()
        })

    flash('Cotação lançada com sucesso!', 'success')
    return redirect(url_for('main.index'))


@pedidos_bp.route('/cotacoes/<int:cotacao_id>/excluir', methods=['POST'])
def excluir_cotacao(cotacao_id):
    cotacao = CotacaoFrete.query.get_or_404(cotacao_id)
    pedido = Pedido.query.get_or_404(cotacao.pedido_id)

    if pedido.status != 'em_cotacao':
        mensagem = 'Só é possível excluir cotações enquanto o pedido estiver em cotação.'
        return jsonify({'sucesso': False, 'mensagem': mensagem}), 400

    db.session.delete(cotacao)
    db.session.commit()

    return jsonify({'sucesso': True, 'mensagem': 'Cotação excluída com sucesso.'})


# 3. Selecionar Cotação Vencedora e Atualizar Status do Pedido para 'aguardando_coleta'
@pedidos_bp.route('/cotacoes/<int:cotacao_id>/selecionar_vencedora', methods=['POST'])
def selecionar_vencedora(cotacao_id):
    cotacao = CotacaoFrete.query.get_or_404(cotacao_id)
    pedido = Pedido.query.get_or_404(cotacao.pedido_id)

    dados = request.get_json(silent=True) or request.form
    justificativa = (dados.get('justificativa') or '').strip()
    menor_valor = db.session.query(db.func.min(CotacaoFrete.valor_frete)).filter_by(
        pedido_id=pedido.id
    ).scalar()

    if menor_valor is not None and cotacao.valor_frete > menor_valor and not justificativa:
        mensagem = 'É necessário informar uma justificativa para escolher uma cotação mais cara.'
        return jsonify({
            'sucesso': False,
            'solicitar_justificativa': True,
            'mensagem': mensagem
        }), 400

    # Desmarca qualquer outra cotação vinculada a este pedido
    CotacaoFrete.query.filter_by(pedido_id=pedido.id).update({'aprovada': False})

    # Define esta cotação como aprovada/vencedora
    cotacao.aprovada = True
    cotacao.observacao = justificativa or None

    # Move o card no Kanban alterando o status do pedido para 'aguardando_coleta'
    pedido.status = 'aguardando_coleta'

    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'sucesso': True, 'mensagem': 'Cotação definida como vencedora com sucesso!'})

    flash('Cotação vencedora selecionada! Pedido movido para Aguardando Coleta.', 'success')
    return redirect(url_for('main.index'))


@pedidos_bp.route('/<int:pedido_id>/datas', methods=['POST'])
def salvar_datas_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    cotacao_vencedora = CotacaoFrete.query.filter_by(
        pedido_id=pedido.id,
        aprovada=True
    ).first()

    if not cotacao_vencedora:
        mensagem = 'Selecione uma cotação vencedora antes de informar as datas.'
        return jsonify({'sucesso': False, 'mensagem': mensagem}), 400

    dados = request.get_json(silent=True) or request.form
    data_coleta_texto = dados.get('data_coleta')
    data_entrega_texto = dados.get('data_entrega')

    if not data_coleta_texto or not data_entrega_texto:
        return jsonify({'sucesso': False, 'mensagem': 'Informe as datas de coleta e de entrega.'}), 400

    try:
        data_coleta = datetime.strptime(data_coleta_texto, '%Y-%m-%d').date()
        data_entrega = datetime.strptime(data_entrega_texto, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'sucesso': False, 'mensagem': 'Informe datas válidas para coleta e entrega.'}), 400

    if data_entrega < data_coleta:
        return jsonify({'sucesso': False, 'mensagem': 'A data de entrega não pode ser anterior à data de coleta.'}), 400

    coleta_foi_adiada = (
        pedido.status == 'em_transito'
        and pedido.data_coleta is not None
        and data_coleta > pedido.data_coleta
    )

    pedido.data_coleta = data_coleta
    pedido.data_entrega = data_entrega
    if coleta_foi_adiada:
        pedido.status = 'aguardando_coleta'
    db.session.commit()

    return jsonify({
        'sucesso': True,
        'mensagem': 'Datas salvas com sucesso.',
        'status': pedido.status
    })


@pedidos_bp.route('/<int:pedido_id>/confirmar-entrega', methods=['POST'])
def confirmar_entrega(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    dados = request.get_json(silent=True) or request.form
    decisao = (dados.get('decisao') or '').strip().lower()
    observacao = (dados.get('observacao_ocorrencia') or '').strip()

    status_anterior = pedido.status
    if status_anterior not in {'em_transito', 'ocorrencia'}:
        return jsonify({
            'sucesso': False,
            'mensagem': 'A confirmação só está disponível para pedidos em trânsito ou em ocorrência.'
        }), 400

    if status_anterior == 'em_transito' and (not pedido.data_entrega or pedido.data_entrega > datetime.utcnow().date()):
        return jsonify({
            'sucesso': False,
            'mensagem': 'A confirmação estará disponível a partir da data prevista de entrega.'
        }), 400

    if decisao not in {'entregue', 'ocorrencia'}:
        return jsonify({'sucesso': False, 'mensagem': 'Informe uma decisão válida.'}), 400

    if status_anterior == 'ocorrencia' and decisao != 'entregue':
        return jsonify({
            'sucesso': False,
            'mensagem': 'Um pedido em ocorrência só pode ser confirmado como entregue.'
        }), 400

    if decisao == 'ocorrencia' and not observacao:
        return jsonify({
            'sucesso': False,
            'mensagem': 'Descreva a ocorrência ou sinistro antes de continuar.'
        }), 400

    pedido.status = decisao
    pedido.data_confirmacao_entrega = datetime.utcnow()
    if decisao == 'ocorrencia':
        pedido.observacao_ocorrencia = observacao
    db.session.commit()

    return jsonify({
        'sucesso': True,
        'mensagem': 'Entrega confirmada com sucesso.' if decisao == 'entregue' else 'Ocorrência registrada com sucesso.',
        'status': pedido.status
    })


# 4. Reverter Cotação Vencedora e Retornar Status do Pedido para 'em_cotacao'
@pedidos_bp.route('/cotacoes/<int:cotacao_id>/reverter_vencedora', methods=['POST'])
def reverter_vencedora(cotacao_id):
    cotacao = CotacaoFrete.query.get_or_404(cotacao_id)
    pedido = Pedido.query.get_or_404(cotacao.pedido_id)

    # Desmarca todas as cotações deste pedido como aprovadas
    CotacaoFrete.query.filter_by(pedido_id=pedido.id).update({'aprovada': False})

    # Retorna o status do pedido para 'em_cotacao'
    pedido.status = 'em_cotacao'
    pedido.data_coleta = None
    pedido.data_entrega = None

    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'sucesso': True, 'mensagem': 'Seleção revertida. O pedido retornou para Em Cotação.'})

    flash('Seleção de cotação revertida! Pedido retornou para Em Cotação.', 'info')
    return redirect(url_for('main.index'))


# 5. Gerenciar Anexos (Upload e Consulta em JSON)
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

    anexos = Anexo.query.filter_by(pedido_id=pedido_id).all()
    return jsonify([{
        'id': a.id,
        'tipo_documento': a.tipo_documento,
        'nome_arquivo': a.nome_arquivo,
        'data_upload': a.data_upload.strftime('%d/%m/%Y %H:%M') if a.data_upload else ''
    } for a in anexos])


# 6. Download / Exibição de Anexos
@pedidos_bp.route('/uploads/<filename>')
def download_anexo(filename):
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    return send_from_directory(upload_folder, filename)