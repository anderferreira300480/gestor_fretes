from flask import Flask   # O flask pe responsável pelas requisições entre o código e o navegador
from flask_sqlalchemy import SQLAlchemy  # O SQLAlchemy faz a ponte de cominicação entre o código e o BD, sem precisar escrever SQL puro
from datetime import datetime   # O "datetime" é voltado para manipulação de datas, horários e fusos horários

app = Flask(__name__)

# Configura o local do arquivo SQLite (será criado na pasta 'instance')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fretes.db' 
app.config['SQLACHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o ORM SQLAlchemy vinculado ao app
db = SQLAlchemy(app)


class Empresa(db.Model):
    __tablename__ = 'empresas'

    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(150), nullable=False)
    nome_fantasia = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(20), unique=True, nullable=False)
    unidade = db.Column(db.String(50), nullable=True)

    # Permite acessar todos os pedidos desta empresa através de 'empresa.pedidos'
    pedidos = db.relationship('Pedido', backref='empresa', lazy=True)

class Transportadora(db.Model):
    __tablename__ = 'transportadoras'

    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)

    # Permite acessar todas as cotações feitas por esta transportadora
    cotacoes = db.relationship('CotacaoFrete', backref='transportadora', lazy=True)