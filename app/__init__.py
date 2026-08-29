# app/__init__.py
from flask import Flask
from app.database import db

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sua_chave_secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestor.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Importação das rotas
    from app.routes.main import main_bp
    from app.routes.pedidos import pedidos_bp
    from app.routes.cotacoes import cotacoes_bp
    from app.routes.cadastros import cadastros_bp

    # Registro das rotas
    app.register_blueprint(main_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(cotacoes_bp)
    app.register_blueprint(cadastros_bp)

    print("--- BLUEPRINT DE CADASTROS REGISTRADO COM SUCESSO ---")

    with app.app_context():
        db.create_all()

    return app