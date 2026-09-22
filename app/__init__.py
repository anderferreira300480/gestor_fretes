"""Configuração e fábrica da aplicação Flask.

Este módulo concentra a criação do objeto Flask, a configuração do banco,
o registro das rotas e a preparação inicial do schema local.
"""

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

    for coluna in ('data_coleta', 'data_entrega'):
        if coluna not in colunas_pedidos:
            db.session.execute(text(f'ALTER TABLE pedidos ADD COLUMN {coluna} DATE'))

    colunas_cotacoes = {
        coluna['name']
        for coluna in db.session.execute(text('PRAGMA table_info(cotacoes)')).mappings()
    }
    if 'observacao' not in colunas_cotacoes:
        db.session.execute(text('ALTER TABLE cotacoes ADD COLUMN observacao TEXT'))

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