# app/routes/cadastros.py
import re
from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models import Empresa, Transportadora, Fornecedor

cadastros_bp = Blueprint('cadastros', __name__, url_prefix='/cadastros')

def apenas_numeros(valor):
    if not valor:
        return ''
    return re.sub(r'\D', '', valor)


@cadastros_bp.route('/verificar-cnpj', methods=['GET'])
def verificar_cnpj():
    cnpj = apenas_numeros(request.args.get('cnpj', ''))
    tipo = request.args.get('tipo', '')

    if not cnpj or len(cnpj) != 14:
        return jsonify({'existe': False})

    existe = False
    if tipo == 'empresa':
        existe = db.session.query(Empresa.id).filter_by(cnpj=cnpj).first() is not None
    elif tipo == 'transportadora':
        existe = db.session.query(Transportadora.id).filter_by(cnpj=cnpj).first() is not None
    elif tipo == 'fornecedor':
        existe = db.session.query(Fornecedor.id).filter_by(cnpj=cnpj).first() is not None

    return jsonify({'existe': existe})


# --- EMPRESAS ---
@cadastros_bp.route('/empresas', methods=['GET', 'POST'], strict_slashes=False)
def empresas():
    erro = None
    if request.method == 'POST':
        cnpj_limpo = apenas_numeros(request.form.get('cnpj'))
        empresa_existente = Empresa.query.filter_by(cnpj=cnpj_limpo).first()
        
        if empresa_existente:
            erro = "Empresa/Filial com este CNPJ já está cadastrada no sistema!"
        else:
            nova_empresa = Empresa(
                razao_social=request.form.get('razao_social'),
                cnpj=cnpj_limpo,
                endereco=request.form.get('endereco'),
                numero=request.form.get('numero'),
                bairro=request.form.get('bairro'),
                cidade=request.form.get('cidade'),
                estado=request.form.get('estado'),
                nome_contato=request.form.get('nome_contato'),
                email=request.form.get('email'),
                telefone=apenas_numeros(request.form.get('telefone'))
            )
            db.session.add(nova_empresa)
            db.session.commit()

    empresas_list = Empresa.query.all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('cadastros/empresas.html', empresas=empresas_list, erro=erro)
    
    return render_template('base.html', empresas=empresas_list, erro=erro, tela_ativa='empresas')


# --- TRANSPORTADORAS ---
@cadastros_bp.route('/transportadoras', methods=['GET', 'POST'], strict_slashes=False)
def transportadoras():
    erro = None
    if request.method == 'POST':
        cnpj_limpo = apenas_numeros(request.form.get('cnpj'))
        transp_existente = Transportadora.query.filter_by(cnpj=cnpj_limpo).first()
        
        if transp_existente:
            erro = "Transportadora com este CNPJ já está cadastrada no sistema!"
        else:
            nova_transp = Transportadora(
                razao_social=request.form.get('razao_social'),
                cnpj=cnpj_limpo,
                endereco=request.form.get('endereco'),
                numero=request.form.get('numero'),
                bairro=request.form.get('bairro'),
                cidade=request.form.get('cidade'),
                estado=request.form.get('estado'),
                nome_contato=request.form.get('nome_contato'),
                email=request.form.get('email'),
                telefone=apenas_numeros(request.form.get('telefone'))
            )
            db.session.add(nova_transp)
            db.session.commit()

    transportadoras_list = Transportadora.query.all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('cadastros/transportadoras.html', transportadoras=transportadoras_list, erro=erro)
    
    return render_template('base.html', transportadoras=transportadoras_list, erro=erro, tela_ativa='transportadoras')


# --- FORNECEDORES ---
@cadastros_bp.route('/fornecedores', methods=['GET', 'POST'], strict_slashes=False)
def fornecedores():
    erro = None
    if request.method == 'POST':
        cnpj_limpo = apenas_numeros(request.form.get('cnpj'))
        forn_existente = Fornecedor.query.filter_by(cnpj=cnpj_limpo).first()
        
        if forn_existente:
            erro = "Fornecedor com este CNPJ já está cadastrado no sistema!"
        else:
            novo_forn = Fornecedor(
                razao_social=request.form.get('razao_social'),
                cnpj=cnpj_limpo,
                endereco=request.form.get('endereco'),
                numero=request.form.get('numero'),
                bairro=request.form.get('bairro'),
                cidade=request.form.get('cidade'),
                estado=request.form.get('estado'),
                nome_contato=request.form.get('nome_contato'),
                email=request.form.get('email'),
                telefone=apenas_numeros(request.form.get('telefone'))
            )
            db.session.add(novo_forn)
            db.session.commit()

    fornecedores_list = Fornecedor.query.all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('cadastros/fornecedores.html', fornecedores=fornecedores_list, erro=erro)
    
    return render_template('base.html', fornecedores=fornecedores_list, erro=erro, tela_ativa='fornecedores')