"""Configuração e fábrica da aplicação Flask.

Este módulo concentra a criação do objeto Flask, a configuração do banco,
o registro das rotas e a preparação inicial do schema local.
"""

import os
from flask import Flask
from app.database import db
from sqlalchemy import text


def _atualizar_schema():
    """Adiciona colunas novas ao SQLite já existente.

    É uma migração manual simples para instalações locais antigas. Ela evita
    que a aplicação quebre quando o modelo ganha campos novos, mas não
    substitui uma ferramenta de migrações versionadas em produção.
    """
    colunas_pedidos = {
        coluna['name']
        for coluna in db.session.execute(text('PRAGMA table_info(pedidos)')).mappings()
    }

    for coluna in ('data_coleta', 'data_entrega', 'nome_contato_fornecedor', 'email_fornecedor', 'telefone_fornecedor'):
        if coluna not in colunas_pedidos:
            tipo = 'DATE' if coluna in {'data_coleta', 'data_entrega'} else 'VARCHAR(120)' if coluna in {'nome_contato_fornecedor', 'email_fornecedor'} else 'VARCHAR(30)'
            db.session.execute(text(f'ALTER TABLE pedidos ADD COLUMN {coluna} {tipo}'))

    colunas_cotacoes = {
        coluna['name']
        for coluna in db.session.execute(text('PRAGMA table_info(cotacoes)')).mappings()
    }
    if 'observacao' not in colunas_cotacoes:
        db.session.execute(text('ALTER TABLE cotacoes ADD COLUMN observacao TEXT'))

    novos_campos_cotacao = {
        'status': "VARCHAR(30) NOT NULL DEFAULT 'respondida'",
        'data_envio': 'DATETIME',
        'erro_envio': 'TEXT',
        'observacao_resposta': 'TEXT',
        'data_resposta': 'DATETIME',
        'token_resposta_hash': 'VARCHAR(64)',
        'token_expira_em': 'DATETIME',
        'token_aprovacao_hash': 'VARCHAR(64)',
        'token_aprovacao_expira_em': 'DATETIME',
        'data_resposta_aprovacao': 'DATETIME'
    }
    for coluna, tipo in novos_campos_cotacao.items():
        if coluna not in colunas_cotacoes:
            db.session.execute(text(f'ALTER TABLE cotacoes ADD COLUMN {coluna} {tipo}'))
    db.session.execute(text(
        'CREATE UNIQUE INDEX IF NOT EXISTS uq_cotacoes_token_resposta_hash '
        'ON cotacoes (token_resposta_hash)'
    ))
    db.session.execute(text(
        'CREATE UNIQUE INDEX IF NOT EXISTS uq_cotacoes_token_aprovacao_hash '
        'ON cotacoes (token_aprovacao_hash)'
    ))

    colunas_pedidos = {
        coluna['name']
        for coluna in db.session.execute(text('PRAGMA table_info(pedidos)')).mappings()
    }
    novos_campos_pedido = {
        'volumes': 'INTEGER',
        'peso_kg': 'FLOAT',
        'dim_altura': 'FLOAT',
        'dim_largura': 'FLOAT',
        'dim_comprimento': 'FLOAT',
        'observacoes': 'TEXT',
        'data_confirmacao_entrega': 'DATETIME',
        'arquivado_em': 'DATETIME',
        'observacao_ocorrencia': 'TEXT'
    }
    for coluna, tipo in novos_campos_pedido.items():
        if coluna not in colunas_pedidos:
            db.session.execute(text(f'ALTER TABLE pedidos ADD COLUMN {coluna} {tipo}'))

    db.session.commit()

def create_app():
    """Cria e configura uma instância independente da aplicação Flask."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sua_chave_secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestor.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SMTP_HOST'] = os.environ.get('SMTP_HOST')
    app.config['SMTP_PORT'] = int(os.environ.get('SMTP_PORT', '587'))
    app.config['SMTP_USERNAME'] = os.environ.get('SMTP_USERNAME')
    app.config['SMTP_PASSWORD'] = os.environ.get('SMTP_PASSWORD')
    app.config['SMTP_SENDER'] = os.environ.get('SMTP_SENDER') or app.config['SMTP_USERNAME']
    app.config['SMTP_USE_TLS'] = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
    app.config['SMTP_USE_SSL'] = os.environ.get('SMTP_USE_SSL', 'false').lower() == 'true'
    app.config['PUBLIC_BASE_URL'] = os.environ.get('PUBLIC_BASE_URL')

    db.init_app(app)

    # Importar os blueprints dentro da fábrica evita ciclos de importação e
    # mantém cada conjunto de endpoints organizado no próprio módulo.
    from app.routes.main import main_bp
    from app.routes.pedidos import pedidos_bp
    from app.routes.cotacoes import cotacoes_bp
    from app.routes.cadastros import cadastros_bp

    # Registrar os blueprints torna suas rotas disponíveis no app principal.
    app.register_blueprint(main_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(cotacoes_bp)
    app.register_blueprint(cadastros_bp)

    print("--- BLUEPRINT DE CADASTROS REGISTRADO COM SUCESSO ---")

    with app.app_context():
        # Cria tabelas ausentes e depois aplica as colunas adicionadas ao longo
        # da evolução do protótipo.
        db.create_all()
        _atualizar_schema()

    return app