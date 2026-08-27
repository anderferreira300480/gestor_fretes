from datetime import datetime
from app.database import db

class Empresa(db.Model):
    __tablename__ = 'empresas'

    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    
    pedidos = db.relationship('Pedido', backref='empresa', lazy=True)


class Transportadora(db.Model):
    __tablename__ = 'transportadoras'

    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    contato = db.Column(db.String(100), nullable=True)
    
    cotacoes = db.relationship('CotacaoFrete', backref='transportadora', lazy=True)


class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id = db.Column(db.Integer, primary_key=True)
    numero_pedido_compra = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fornecedor = db.Column(db.String(150), nullable=False)
    valor_mercadoria = db.Column(db.Float, nullable=True)
    peso_kg = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(30), default='Em Cotação', nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    cotacoes = db.relationship('CotacaoFrete', backref='pedido', lazy=True, cascade="all, delete-orphan")


class CotacaoFrete(db.Model):
    __tablename__ = 'cotacoes_fretes'

    id = db.Column(db.Integer, primary_key=True)
    valor_cotado = db.Column(db.Float, nullable=False)
    prazo_dias = db.Column(db.Integer, nullable=False)
    observacoes = db.Column(db.String(255), nullable=True)
    vencedor = db.Column(db.Boolean, default=False, nullable=False)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)

    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    transportadora_id = db.Column(db.Integer, db.ForeignKey('transportadoras.id'), nullable=False)