"""Rotas do ciclo de vida dos pedidos, cotações e anexos."""

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app, make_response
from werkzeug.utils import secure_filename
from app.database import db
from app.models import Empresa, Fornecedor, Pedido, CotacaoFrete, Anexo, Transportadora
from app.email_service import (
    EmailAttachmentError,
    EmailConfigurationError,
    EmailDeliveryError,
    enviar_solicitacao_cotacao
)

pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'xml', 'zip', 'doc', 'docx'}

def allowed_file(filename):
    """Verifica a extensão permitida antes de salvar um upload."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@pedidos_bp.route('/api/empresa/<int:empresa_id>', methods=['GET'])
def obter_empresa(empresa_id):
    """Fornece endereço e contato da empresa para autopreenchimento."""
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
    """Fornece endereço e contato do fornecedor para autopreenchimento."""
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
    """Exibe o formulário ou cria um pedido no status inicial de cotação."""
    if request.method == 'POST':
        empresa_id = request.form.get('empresa_id')
        fornecedor_id = request.form.get('fornecedor_id')
        
        numero_pedido_compra = request.form.get('numero_pedido_compra') or request.form.get('numero_pedido')
        valor_mercadoria = request.form.get('valor_mercadoria') or request.form.get('valor_carga') or 0.0

        # Campos dimensionais são opcionais; vazios viram None no banco.
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
    """Mantém uma URL alternativa usada por formulários antigos."""
    return novo_pedido()


@pedidos_bp.route('/<int:pedido_id>/excluir', methods=['POST'])
def excluir_pedido(pedido_id):
    """Exclui um pedido e seus registros relacionados via cascade do modelo."""
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
    """Monta o JSON consumido pelo modal de cotações do Kanban."""
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
            'observacao': c.observacao or '',
            'status': c.status,
            'data_envio': c.data_envio.isoformat() if c.data_envio else '',
            'erro_envio': c.erro_envio or '',
            'observacao_resposta': c.observacao_resposta or '',
            'data_resposta': c.data_resposta.isoformat() if c.data_resposta else ''
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
    """Adiciona uma proposta enquanto o pedido ainda está em cotação."""
    pedido = Pedido.query.get_or_404(pedido_id)
    
    if pedido.status != 'em_cotacao':
        flash('Não é possível adicionar novas cotações para este pedido pois a cotação já foi encerrada.', 'warning')
        return redirect(url_for('main.index'))

    transportadora_id = request.form.get('transportadora_id', type=int)
    valor_frete_texto = (request.form.get('valor_frete') or '').strip()
    prazo_dias = request.form.get('prazo_dias')

    transportadora = db.session.get(Transportadora, transportadora_id) if transportadora_id else None
    if not transportadora:
        return jsonify({'sucesso': False, 'mensagem': 'Selecione uma transportadora válida.'}), 400

    try:
        valor_frete = float(valor_frete_texto) if valor_frete_texto else 0.0
        prazo_dias_numero = int(prazo_dias) if prazo_dias else None
    except ValueError:
        return jsonify({'sucesso': False, 'mensagem': 'Informe um valor e prazo válidos.'}), 400
    if valor_frete < 0 or (prazo_dias_numero is not None and prazo_dias_numero < 0):
        return jsonify({'sucesso': False, 'mensagem': 'Valor e prazo não podem ser negativos.'}), 400

    nova_cotacao = CotacaoFrete(
        pedido_id=pedido_id,
        transportadora_id=transportadora.id,
        valor_frete=valor_frete,
        prazo_dias=prazo_dias_numero,
        aprovada=False,
        status='respondida' if valor_frete_texto else 'pendente_envio'
    )
    db.session.add(nova_cotacao)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'sucesso': True,
            'mensagem': 'Cotação adicionada com sucesso.' if valor_frete_texto else 'Solicitação de cotação adicionada.',
            'pedido_id': pedido.id,
            'cotacoes_count': CotacaoFrete.query.filter_by(pedido_id=pedido.id).count()
        })

    flash('Cotação lançada com sucesso!', 'success')
    return redirect(url_for('main.index'))


@pedidos_bp.route('/cotacoes/<int:cotacao_id>/enviar', methods=['POST'])
def enviar_cotacao(cotacao_id):
    """Envia a solicitação da cotação e o Pedido de Compra por e-mail."""
    cotacao = CotacaoFrete.query.get_or_404(cotacao_id)
    pedido = cotacao.pedido

    if pedido.status != 'em_cotacao':
        return jsonify({'sucesso': False, 'mensagem': 'O pedido não está mais na etapa de cotação.'}), 400
    if cotacao.status not in ('pendente_envio', 'erro_envio'):
        return jsonify({'sucesso': False, 'mensagem': 'Esta solicitação já foi enviada ou não está pendente.'}), 400

    token = secrets.token_urlsafe(32)
    cotacao.token_resposta_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    cotacao.token_expira_em = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    base_url = (current_app.config.get('PUBLIC_BASE_URL') or request.url_root).rstrip('/')
    url_resposta = f'{base_url}{url_for("pedidos.responder_cotacao", token=token)}'

    try:
        enviar_solicitacao_cotacao(cotacao, url_resposta)
    except (EmailAttachmentError, EmailConfigurationError, EmailDeliveryError) as erro:
        cotacao.status = 'erro_envio'
        cotacao.erro_envio = str(erro)
        db.session.commit()
        return jsonify({'sucesso': False, 'mensagem': cotacao.erro_envio}), 400

    cotacao.status = 'enviada'
    cotacao.data_envio = datetime.utcnow()
    cotacao.erro_envio = None
    db.session.commit()

    return jsonify({'sucesso': True, 'mensagem': 'Solicitação enviada por e-mail.'})


@pedidos_bp.route('/cotacoes/<int:cotacao_id>/editar', methods=['POST'])
def editar_cotacao(cotacao_id):
    """Atualiza uma proposta respondida enquanto o pedido ainda está em cotação."""
    cotacao = CotacaoFrete.query.get_or_404(cotacao_id)
    pedido = cotacao.pedido

    if pedido.status != 'em_cotacao' or cotacao.aprovada:
        return jsonify({
            'sucesso': False,
            'mensagem': 'Só é possível editar cotações antes de selecionar a vencedora.'
        }), 400
    if cotacao.status != 'respondida':
        return jsonify({
            'sucesso': False,
            'mensagem': 'Somente cotações respondidas podem ser editadas.'
        }), 400

    dados = request.get_json(silent=True) or request.form
    try:
        valor_frete = Decimal(str(dados.get('valor_frete') or '').strip())
        prazo_dias = int(str(dados.get('prazo_dias') or '').strip())
    except (InvalidOperation, ValueError):
        return jsonify({'sucesso': False, 'mensagem': 'Informe um valor e prazo válidos.'}), 400

    if not valor_frete.is_finite() or valor_frete <= 0:
        return jsonify({'sucesso': False, 'mensagem': 'O valor do frete deve ser maior que zero.'}), 400
    if prazo_dias < 1:
        return jsonify({'sucesso': False, 'mensagem': 'O prazo deve ser de pelo menos 1 dia.'}), 400

    observacao_resposta = str(dados.get('observacao') or '').strip()
    if len(observacao_resposta) > 2000:
        return jsonify({'sucesso': False, 'mensagem': 'A observação deve ter no máximo 2.000 caracteres.'}), 400

    cotacao.valor_frete = float(valor_frete)
    cotacao.prazo_dias = prazo_dias
    cotacao.observacao_resposta = observacao_resposta or None
    db.session.commit()

    return jsonify({'sucesso': True, 'mensagem': 'Cotação atualizada com sucesso.'})


def _renderizar_pagina_resposta(estado, status_code=200, **contexto):
    resposta = make_response(render_template('cotacoes/responder.html', estado=estado, **contexto))
    resposta.status_code = status_code
    resposta.headers['Cache-Control'] = 'no-store'
    resposta.headers['Referrer-Policy'] = 'no-referrer'
    resposta.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return resposta


@pedidos_bp.route('/cotacoes/responder/<token>', methods=['GET', 'POST'])
def responder_cotacao(token):
    """Recebe a proposta da transportadora pelo link enviado por e-mail."""
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    cotacao = CotacaoFrete.query.filter_by(token_resposta_hash=token_hash).first()
    agora = datetime.utcnow()

    if (
        not cotacao
        or cotacao.status != 'enviada'
        or not cotacao.token_expira_em
        or cotacao.token_expira_em <= agora
    ):
        return _renderizar_pagina_resposta('invalido', 410)

    if request.method == 'POST':
        try:
            valor_frete = Decimal((request.form.get('valor_frete') or '').strip())
            prazo_dias = int(request.form.get('prazo_dias', ''))
        except (InvalidOperation, ValueError):
            valor_frete = Decimal('0')
            prazo_dias = 0
            erro = 'Informe um valor de frete e um prazo válidos.'
        else:
            erro = ''
            if not valor_frete.is_finite() or valor_frete <= 0:
                erro = 'O valor do frete deve ser maior que zero.'
            elif prazo_dias < 1:
                erro = 'O prazo deve ser de pelo menos 1 dia.'

        observacao_resposta = (request.form.get('observacao') or '').strip()
        if len(observacao_resposta) > 2000:
            erro = 'A observação deve ter no máximo 2.000 caracteres.'

        if erro:
            return _renderizar_pagina_resposta(
                'formulario',
                cotacao=cotacao,
                erro=erro,
                valor_frete=request.form.get('valor_frete', ''),
                prazo_dias=request.form.get('prazo_dias', ''),
                observacao=observacao_resposta
            )

        cotacao.valor_frete = float(valor_frete)
        cotacao.prazo_dias = prazo_dias
        cotacao.observacao_resposta = observacao_resposta or None
        cotacao.data_resposta = agora
        cotacao.status = 'respondida'
        cotacao.token_resposta_hash = None
        cotacao.token_expira_em = None
        db.session.commit()
        return _renderizar_pagina_resposta(
            'sucesso',
            numero_pedido=cotacao.pedido.numero_pedido_compra
        )

    return _renderizar_pagina_resposta('formulario', cotacao=cotacao)


@pedidos_bp.route('/cotacoes/<int:cotacao_id>/excluir', methods=['POST'])
def excluir_cotacao(cotacao_id):
    """Remove uma cotação somente antes do encerramento da cotação."""
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
    """Aprova uma cotação e move o pedido para aguardando coleta.

    Quando a proposta escolhida não é a mais barata, a justificativa enviada
    pelo usuário torna-se obrigatória e é armazenada na própria cotação.
    """
    cotacao = CotacaoFrete.query.get_or_404(cotacao_id)
    pedido = Pedido.query.get_or_404(cotacao.pedido_id)

    if cotacao.status != 'respondida':
        mensagem = 'Somente cotações respondidas podem ser selecionadas como vencedoras.'
        return jsonify({'sucesso': False, 'mensagem': mensagem}), 400

    dados = request.get_json(silent=True) or request.form
    justificativa = (dados.get('justificativa') or '').strip()
    menor_valor = db.session.query(db.func.min(CotacaoFrete.valor_frete)).filter_by(
        pedido_id=pedido.id,
        status='respondida'
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
    """Salva coleta/entrega e atualiza a etapa quando o prazo muda.

    Uma nova data de coleta posterior reabre a coleta. Para um pedido em
    ocorrência, uma nova data de entrega posterior à anterior representa uma
    nova programação de transporte e devolve o pedido para ``em_transito``.
    """
    pedido = Pedido.query.get_or_404(pedido_id)
    
    if pedido.status == 'entregue':
        return jsonify({
            'sucesso': False,
            'mensagem': 'Não é possível editar as datas de um pedido entregue.'
        }), 400
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
    entrega_foi_reprogramada = (
        pedido.status == 'ocorrencia'
        and pedido.data_entrega is not None
        and data_entrega > pedido.data_entrega
    )

    pedido.data_coleta = data_coleta
    pedido.data_entrega = data_entrega
    if coleta_foi_adiada:
        pedido.status = 'aguardando_coleta'
    elif entrega_foi_reprogramada:
        pedido.status = 'em_transito'
    db.session.commit()

    return jsonify({
        'sucesso': True,
        'mensagem': 'Datas salvas com sucesso.',
        'status': pedido.status
    })


@pedidos_bp.route('/<int:pedido_id>/confirmar-entrega', methods=['POST'])
def confirmar_entrega(pedido_id):
    """Confirma entrega ou registra ocorrência após a data prevista."""
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
    """Desfaz a seleção e devolve o pedido para a etapa de cotação."""
    cotacao = CotacaoFrete.query.get_or_404(cotacao_id)
    pedido = Pedido.query.get_or_404(cotacao.pedido_id)

    if pedido.status == 'entregue':
        mensagem = 'Não é possível reverter a cotação de um pedido entregue.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'sucesso': False, 'mensagem': mensagem}), 400
        flash(mensagem, 'warning')
        return redirect(url_for('main.index'))

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
    """Lista anexos ou salva um novo arquivo associado ao pedido."""
    if request.method == 'POST':
        tipo_documento = request.form.get('tipo_documento')
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo enviado', 'danger')
            return redirect(url_for('main.index'))

        file = request.files['arquivo']
        if file and allowed_file(file.filename):
            # Os arquivos ficam fora de instance para poderem ser servidos pela
            # rota de download e organizados por instalação.
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
    """Entrega um arquivo já salvo na pasta de uploads."""
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    return send_from_directory(upload_folder, filename)