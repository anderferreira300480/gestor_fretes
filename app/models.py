from app.database import db

# MODELO EMPRESA (Unidade Compradora)
class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(20), unique=True, nullable=False)
    endereco = db.Column(db.String(150), nullable=True)
    numero = db.Column(db.String(20), nullable=True)
    bairro = db.Column(db.String(80), nullable=True)
    cidade = db.Column(db.String(80), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    nome_contato = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    telefone = db.Column(db.String(30), nullable=True)

# MODELO TRANSPORTADORA
class Transportadora(db.Model):
    __tablename__ = 'transportadoras'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(20), unique=True, nullable=False)
    endereco = db.Column(db.String(150), nullable=True)
    numero = db.Column(db.String(20), nullable=True)
    bairro = db.Column(db.String(80), nullable=True)
    cidade = db.Column(db.String(80), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    nome_contato = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    telefone = db.Column(db.String(30), nullable=True)

# MODELO FORNECEDOR
class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(20), unique=True, nullable=False)
    endereco = db.Column(db.String(150), nullable=True)
    numero = db.Column(db.String(20), nullable=True)
    bairro = db.Column(db.String(80), nullable=True)
    cidade = db.Column(db.String(80), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    nome_contato = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    telefone = db.Column(db.String(30), nullable=True)

# MODELO PEDIDO DE COMPRA
class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    numero_pedido_compra = db.Column(db.String(50), nullable=False)
    
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    empresa = db.relationship('Empresa', backref='pedidos')

    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    fornecedor = db.relationship('Fornecedor', backref='pedidos')

    valor_mercadoria = db.Column(db.Float, nullable=True)
    peso_kg = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='Em Cotação')
    
    # Contato manual do responsável na Empresa Compradora
    empresa_contato_nome = db.Column(db.String(100), nullable=True)
    empresa_contato_email = db.Column(db.String(100), nullable=True)
    empresa_contato_telefone = db.Column(db.String(30), nullable=True)

# MODELO COTAÇÃO DE FRETE
class CotacaoFrete(db.Model):
    __tablename__ = 'cotacoes_frete'
    id = db.Column(db.Integer, primary_key=True)
    
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    pedido = db.relationship('Pedido', backref='cotacoes')

    transportadora_id = db.Column(db.Integer, db.ForeignKey('transportadoras.id'), nullable=False)
    transportadora = db.relationship('Transportadora', backref='cotacoes')

    valor_frete = db.Column(db.Float, nullable=False)
    prazo_dias = db.Column(db.Integer, nullable=False)
    vencedora = db.Column(db.Boolean, default=False)
    data_cotacao = db.Column(db.DateTime, default=db.func.current_timestamp())