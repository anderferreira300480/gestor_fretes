"""Envio de solicitações de cotação por SMTP."""

import mimetypes
import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app

from app.models import Anexo


class EmailConfigurationError(Exception):
    """Configuração de e-mail ausente ou inválida."""


class EmailAttachmentError(Exception):
    """Pedido de compra não encontrado ou indisponível."""


class EmailDeliveryError(Exception):
    """Falha na entrega SMTP."""


def _valor_brasileiro(valor, casas=2):
    return f'{valor:,.{casas}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def enviar_solicitacao_cotacao(cotacao, url_resposta):
    """Envia os dados do pedido e o anexo Pedido de Compra à transportadora."""
    pedido = cotacao.pedido
    transportadora = cotacao.transportadora

    if not transportadora or not transportadora.email or '@' not in transportadora.email:
        raise EmailConfigurationError('Cadastre um e-mail válido para esta transportadora.')

    anexo = Anexo.query.filter_by(
        pedido_id=pedido.id,
        tipo_documento='Pedido de Compra'
    ).order_by(Anexo.data_upload.desc(), Anexo.id.desc()).first()
    if not anexo:
        raise EmailAttachmentError('Anexe o arquivo do tipo Pedido de Compra antes de enviar.')

    try:
        with open(anexo.caminho_arquivo, 'rb') as arquivo:
            conteudo_anexo = arquivo.read()
    except OSError as erro:
        raise EmailAttachmentError('O arquivo Pedido de Compra não está disponível no servidor.') from erro

    configuracao = current_app.config
    host = configuracao.get('SMTP_HOST')
    remetente = configuracao.get('SMTP_SENDER')
    usuario = configuracao.get('SMTP_USERNAME')
    senha = configuracao.get('SMTP_PASSWORD')
    usar_tls = configuracao.get('SMTP_USE_TLS', True)
    usar_ssl = configuracao.get('SMTP_USE_SSL', False)

    if not host or not remetente:
        raise EmailConfigurationError('Configure SMTP_HOST e SMTP_SENDER para habilitar o envio.')
    if usar_tls and usar_ssl:
        raise EmailConfigurationError('Use SMTP_USE_TLS ou SMTP_USE_SSL, não ambos.')
    if bool(usuario) != bool(senha):
        raise EmailConfigurationError('SMTP_USERNAME e SMTP_PASSWORD devem ser configurados juntos.')

    empresa = pedido.empresa
    fornecedor = pedido.fornecedor
    corpo = [
        f'Olá, {transportadora.nome_contato or "equipe"}.',
        '',
        'Solicitamos uma cotação de frete para o pedido abaixo.',
        f'Pedido de compra: {pedido.numero_pedido_compra}',
        f'Empresa: {empresa.razao_social if empresa else "Não informada"}',
        f'CNPJ da empresa: {empresa.cnpj if empresa else "Não informado"}',
        f'Fornecedor: {fornecedor.razao_social if fornecedor else "Não informado"}',
        f'CNPJ do fornecedor: {fornecedor.cnpj if fornecedor else "Não informado"}',
        f'Valor da mercadoria: R$ {_valor_brasileiro(pedido.valor_mercadoria or 0)}',
        f'Volumes: {pedido.volumes if pedido.volumes is not None else "Não informado"}',
        f'Peso: {_valor_brasileiro(pedido.peso_kg) if pedido.peso_kg is not None else "Não informado"} kg',
        'Dimensões (A x L x C): '
        + ' x '.join(
            _valor_brasileiro(valor, 2) if valor is not None else '-'
            for valor in (pedido.dim_altura, pedido.dim_largura, pedido.dim_comprimento)
        ) + ' m',
        f'Observações: {pedido.observacoes or "Nenhuma"}',
        '',
        'O pedido de compra segue em anexo.',
        'Atenciosamente,',
        empresa.razao_social if empresa else 'Equipe de Logística',
        '',
        'Para informar o valor do frete e o prazo, acesse o formulário seguro:',
        url_resposta
    ]

    mensagem = EmailMessage()
    mensagem['Subject'] = f'Solicitação de cotação de frete - Pedido {pedido.numero_pedido_compra}'
    mensagem['From'] = remetente
    mensagem['To'] = transportadora.email
    mensagem.set_content('\n'.join(corpo))

    tipo_mime, _ = mimetypes.guess_type(anexo.nome_arquivo)
    tipo_mime = tipo_mime or 'application/octet-stream'
    tipo_principal, subtipo = tipo_mime.split('/', 1)
    mensagem.add_attachment(
        conteudo_anexo,
        maintype=tipo_principal,
        subtype=subtipo,
        filename=anexo.nome_arquivo
    )

    try:
        contexto = ssl.create_default_context()
        if usar_ssl:
            with smtplib.SMTP_SSL(
                host,
                configuracao.get('SMTP_PORT', 465),
                context=contexto,
                timeout=30
            ) as servidor:
                if usuario:
                    servidor.login(usuario, senha)
                servidor.send_message(mensagem)
        else:
            with smtplib.SMTP(
                host,
                configuracao.get('SMTP_PORT', 587),
                timeout=30
            ) as servidor:
                servidor.ehlo()
                if usar_tls:
                    servidor.starttls(context=contexto)
                    servidor.ehlo()
                if usuario:
                    servidor.login(usuario, senha)
                servidor.send_message(mensagem)
    except (OSError, smtplib.SMTPException) as erro:
        raise EmailDeliveryError('Não foi possível entregar o e-mail. Verifique o SMTP e tente novamente.') from erro


def enviar_aprovacao_cotacao(cotacao, url_resposta, dados_fornecedor=None):
    """Informa à transportadora que a cotação foi aprovada e pede datas aproximadas."""
    pedido = cotacao.pedido
    transportadora = cotacao.transportadora

    if not transportadora or not transportadora.email or '@' not in transportadora.email:
        raise EmailConfigurationError('Cadastre um e-mail válido para esta transportadora.')

    campos_fornecedor = dados_fornecedor or {}
    nome_fornecedor = (
        (pedido.nome_contato_fornecedor or '').strip()
        or (campos_fornecedor.get('nome_contato_fornecedor') or '').strip()
        or (pedido.fornecedor.nome_contato if pedido.fornecedor else '')
    )
    email_fornecedor = (
        (pedido.email_fornecedor or '').strip()
        or (campos_fornecedor.get('email_fornecedor') or '').strip()
        or (pedido.fornecedor.email if pedido.fornecedor else '')
    )
    telefone_fornecedor = (
        (pedido.telefone_fornecedor or '').strip()
        or (campos_fornecedor.get('telefone_fornecedor') or '').strip()
        or (pedido.fornecedor.telefone if pedido.fornecedor else '')
    )

    configuracao = current_app.config
    host = configuracao.get('SMTP_HOST')
    remetente = configuracao.get('SMTP_SENDER')
    usuario = configuracao.get('SMTP_USERNAME')
    senha = configuracao.get('SMTP_PASSWORD')
    usar_tls = configuracao.get('SMTP_USE_TLS', True)
    usar_ssl = configuracao.get('SMTP_USE_SSL', False)

    if not host or not remetente:
        raise EmailConfigurationError('Configure SMTP_HOST e SMTP_SENDER para habilitar o envio.')
    if usar_tls and usar_ssl:
        raise EmailConfigurationError('Use SMTP_USE_TLS ou SMTP_USE_SSL, não ambos.')
    if bool(usuario) != bool(senha):
        raise EmailConfigurationError('SMTP_USERNAME e SMTP_PASSWORD devem ser configurados juntos.')

    empresa = pedido.empresa
    fornecedor = pedido.fornecedor
    corpo = [
        f'Olá, {transportadora.nome_contato or "equipe"}.',
        '',
        'Sua proposta foi aprovada para o pedido abaixo.',
        f'Pedido de compra: {pedido.numero_pedido_compra}',
        f'Empresa: {empresa.razao_social if empresa else "Não informada"}',
        f'Fornecedor: {fornecedor.razao_social if fornecedor else "Não informado"}',
        f'Contato do fornecedor: {nome_fornecedor or "Não informado"}',
        f'E-mail do fornecedor: {email_fornecedor or "Não informado"}',
        f'Telefone do fornecedor: {telefone_fornecedor or "Não informado"}',
        '',
        'Favor entrar em contato com o fornecedor para alinhar a coleta e a entrega.',
        '',
        'Para informar a previsão de coleta e entrega, acesse o formulário:',
        url_resposta,
        '',
        'Atenciosamente,',
        empresa.razao_social if empresa else 'Equipe de Logística'
    ]

    mensagem = EmailMessage()
    mensagem['Subject'] = f'Cotação aprovada - Pedido {pedido.numero_pedido_compra}'
    mensagem['From'] = remetente
    mensagem['To'] = transportadora.email
    mensagem.set_content('\n'.join(corpo))

    try:
        contexto = ssl.create_default_context()
        if usar_ssl:
            with smtplib.SMTP_SSL(
                host,
                configuracao.get('SMTP_PORT', 465),
                context=contexto,
                timeout=30
            ) as servidor:
                if usuario:
                    servidor.login(usuario, senha)
                servidor.send_message(mensagem)
        else:
            with smtplib.SMTP(
                host,
                configuracao.get('SMTP_PORT', 587),
                timeout=30
            ) as servidor:
                servidor.ehlo()
                if usar_tls:
                    servidor.starttls(context=contexto)
                    servidor.ehlo()
                if usuario:
                    servidor.login(usuario, senha)
                servidor.send_message(mensagem)
    except (OSError, smtplib.SMTPException) as erro:
        raise EmailDeliveryError('Não foi possível entregar o e-mail de aprovação. Verifique o SMTP e tente novamente.') from erro