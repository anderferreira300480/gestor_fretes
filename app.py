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

class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id = db.Column(db.Integer, primary_key=True)
    # Rastreável para relatórios futuros com index=True
    numero_pedido_compra = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fornecedor = db.Column(db.String(150), nullable=False)
    valor_mercadoria = db.Column(db.Float, nullable=True)
    peso_kg = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(30), default='Em Cotação', nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Vínculo com a empresa solicitante
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    
    # Permite acessar todas as cotações deste pedido: pedido.cotacoes
    cotacoes = db.relationship('CotacaoFrete', backref='pedido', lazy=True, cascade="all, delete-orphan")


class CotacaoFrete(db.Model):
    __tablename__ = 'cotacoes_fretes'

    id = db.Column(db.Integer, primary_key=True)
    valor_cotado = db.Column(db.Float, nullable=False)
    prazo_dias = db.Column(db.Integer, nullable=False)
    observacoes = db.Column(db.String(255), nullable=True) # Anotações sobre a proposta do e-mail
    vencedor = db.Column(db.Boolean, default=False, nullable=False)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Chaves Estrangeiras (Liga o Pedido à Transportadora que deu a proposta)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    transportadora_id = db.Column(db.Integer, db.ForeignKey('transportadoras.id'), nullable=False)    