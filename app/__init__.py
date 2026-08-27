from flask import Flask
from .database import db

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'chave-secreta-de-desenvolvimento'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestor_fretes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa o banco de dados
    db.init_app(app)

    # Importa e registra as rotas (Blueprints)
    from .routes.main import main_bp
    from .routes.pedidos import pedidos_bp
    from .routes.cotacoes import cotacoes_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(cotacoes_bp)

    # Cria as tabelas do banco automaticamente
    with app.app_context():
        from . import models
        db.create_all()

    return app