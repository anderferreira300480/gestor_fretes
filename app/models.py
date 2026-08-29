# app/models.py
from app.database import db
from datetime import datetime

class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    nome_contato = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(30))
    
    pedidos = db.relationship('Pedido', backref='empresa', lazy=True)

class Transportadora(db.Model):
    __tablename__ = 'transportadoras'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    nome_contato = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(30))

class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    nome_contato = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(30))

    pedidos = db.relationship('Pedido', backref='fornecedor', lazy=True)

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    numero_pedido_compra = db.Column(db.String(50), nullable=False)
    valor_mercadoria = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='em_cotacao')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=True)
    
    cotacoes = db.relationship('CotacaoFrete', backref='pedido', lazy=True, cascade="all, delete-orphan")

class CotacaoFrete(db.Model):
    __tablename__ = 'cotacoes'
    id = db.Column(db.Integer, primary_key=True)
    valor_frete = db.Column(db.Float, nullable=False)
    prazo_dias = db.Column(db.Integer, nullable=True)
    aprovada = db.Column(db.Boolean, default=False)
    
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    transportadora_id = db.Column(db.Integer, db.ForeignKey('transportadoras.id'), nullable=True)
    transportadora = db.relationship('Transportadora', backref='cotacoes', lazy=True)

# Alias de compatibilidade (para evitar erros se algum arquivo ainda utilizar 'Cotacao')
Cotacao = CotacaoFrete