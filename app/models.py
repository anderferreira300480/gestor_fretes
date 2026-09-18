from app.database import db
from datetime import datetime

class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False)
    cep = db.Column(db.String(10))  # Campo de CEP adicionado
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
    cep = db.Column(db.String(10))  # Campo de CEP adicionado
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
    cep = db.Column(db.String(10))  # Campo de CEP adicionado
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
    volumes = db.Column(db.Integer, nullable=True)
    peso_kg = db.Column(db.Float, nullable=True)
    dim_altura = db.Column(db.Float, nullable=True)
    dim_largura = db.Column(db.Float, nullable=True)
    dim_comprimento = db.Column(db.Float, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='em_cotacao')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_coleta = db.Column(db.Date, nullable=True)
    data_entrega = db.Column(db.Date, nullable=True)
    data_confirmacao_entrega = db.Column(db.DateTime, nullable=True)
    observacao_ocorrencia = db.Column(db.Text, nullable=True)
    
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=True)
    
    cotacoes = db.relationship('CotacaoFrete', backref='pedido', lazy=True, cascade="all, delete-orphan")
    anexos = db.relationship('Anexo', backref='pedido', lazy=True, cascade="all, delete-orphan")

class CotacaoFrete(db.Model):
    __tablename__ = 'cotacoes'
    id = db.Column(db.Integer, primary_key=True)
    valor_frete = db.Column(db.Float, nullable=False)
    prazo_dias = db.Column(db.Integer, nullable=True)
    aprovada = db.Column(db.Boolean, default=False)
    observacao = db.Column(db.Text, nullable=True)
    
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    transportadora_id = db.Column(db.Integer, db.ForeignKey('transportadoras.id'), nullable=True)
    transportadora = db.relationship('Transportadora', backref='cotacoes', lazy=True)

class Anexo(db.Model):
    __tablename__ = 'anexos'
    id = db.Column(db.Integer, primary_key=True)
    tipo_documento = db.Column(db.String(50), nullable=False)  # Ex: Nota Fiscal, CTe, Outros
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho_arquivo = db.Column(db.String(255), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)

# Alias de compatibilidade
Cotacao = CotacaoFrete