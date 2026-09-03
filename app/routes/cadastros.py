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


# --- ROTA GENÉRICA PARA CONSULTAR DADOS DO MODAL (VISUALIZAR/EDITAR) ---
@cadastros_bp.route('/api/<tipo>/<int:registro_id>', methods=['GET'])
def obter_registro(tipo, registro_id):
    model_map = {
        'empresa': Empresa,
        'transportadora': Transportadora,
        'fornecedor': Fornecedor
    }
    model = model_map.get(tipo)
    if not model:
        return jsonify({'erro': 'Tipo inválido'}), 400

    item = model.query.get(registro_id)
    if not item:
        return jsonify({'erro': 'Registro não encontrado'}), 404

    return jsonify({
        'id': item.id,
        'razao_social': item.razao_social,
        'cnpj': item.cnpj,
        'cep': item.cep,
        'endereco': item.endereco,
        'numero': item.numero,
        'bairro': item.bairro,
        'cidade': item.cidade,
        'estado': item.estado,
        'nome_contato': item.nome_contato,
        'email': item.email,
        'telefone': item.telefone
    })


# --- ROTA GENÉRICA PARA ATUALIZAR REGISTRO VIA MODAL ---
@cadastros_bp.route('/api/<tipo>/atualizar/<int:registro_id>', methods=['POST'])
def atualizar_registro(tipo, registro_id):
    model_map = {
        'empresa': Empresa,
        'transportadora': Transportadora,
        'fornecedor': Fornecedor
    }
    model = model_map.get(tipo)
    if not model:
        return jsonify({'sucesso': False, 'erro': 'Tipo inválido'}), 400

    item = model.query.get(registro_id)
    if not item:
        return jsonify({'sucesso': False, 'erro': 'Registro não encontrado'}), 404

    try:
        item.razao_social = request.form.get('razao_social')
        item.cep = apenas_numeros(request.form.get('cep'))
        item.endereco = request.form.get('endereco')
        item.numero = request.form.get('numero')
        item.bairro = request.form.get('bairro')
        item.cidade = request.form.get('cidade')
        item.estado = request.form.get('estado')
        item.nome_contato = request.form.get('nome_contato')
        item.email = request.form.get('email')
        item.telefone = apenas_numeros(request.form.get('telefone'))

        db.session.commit()
        return jsonify({
            'sucesso': True,
            'item': {
                'id': item.id,
                'razao_social': item.razao_social,
                'cnpj': item.cnpj,
                'cep': item.cep,
                'endereco': item.endereco,
                'numero': item.numero,
                'bairro': item.bairro,
                'cidade': item.cidade,
                'estado': item.estado,
                'nome_contato': item.nome_contato,
                'email': item.email,
                'telefone': item.telefone
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


# --- EMPRESAS ---
@cadastros_bp.route('/empresas', methods=['GET', 'POST'], strict_slashes=False)
def empresas():
    erro = None
    if request.method == 'POST':
        cnpj_limpo = apenas_numeros(request.form.get('cnpj'))
        empresa_existente = Empresa.query.filter_by(cnpj=cnpj_limpo).first()
        
        if empresa_existente:
            erro = "Empresa/Filial com este CNPJ já está cadastrada no sistema!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'sucesso': False, 'erro': erro}), 400
        else:
            nova_empresa = Empresa(
                razao_social=request.form.get('razao_social'),
                cnpj=cnpj_limpo,
                cep=apenas_numeros(request.form.get('cep')),
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

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({
                    'sucesso': True,
                    'item': {
                        'id': nova_empresa.id,
                        'razao_social': nova_empresa.razao_social,
                        'cnpj': nova_empresa.cnpj,
                        'cep': nova_empresa.cep,
                        'endereco': nova_empresa.endereco,
                        'numero': nova_empresa.numero,
                        'bairro': nova_empresa.bairro,
                        'cidade': nova_empresa.cidade,
                        'estado': nova_empresa.estado,
                        'nome_contato': nova_empresa.nome_contato,
                        'email': nova_empresa.email,
                        'telefone': nova_empresa.telefone
                    }
                })

    empresas_list = Empresa.query.all()
    
    # Se for requisição AJAX (carregarTela do SPA) renderiza apenas o fragmento HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('cadastros/empresas.html', empresas=empresas_list, erro=erro)
    
    # Se for acesso direto pela URL no navegador, renderiza o template base da página
    return render_template('cadastros/empresas.html', empresas=empresas_list, erro=erro)


# --- TRANSPORTADORAS ---
@cadastros_bp.route('/transportadoras', methods=['GET', 'POST'], strict_slashes=False)
def transportadoras():
    erro = None
    if request.method == 'POST':
        cnpj_limpo = apenas_numeros(request.form.get('cnpj'))
        transp_existente = Transportadora.query.filter_by(cnpj=cnpj_limpo).first()
        
        if transp_existente:
            erro = "Transportadora com este CNPJ já está cadastrada no sistema!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'sucesso': False, 'erro': erro}), 400
        else:
            nova_transp = Transportadora(
                razao_social=request.form.get('razao_social'),
                cnpj=cnpj_limpo,
                cep=apenas_numeros(request.form.get('cep')),
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

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({
                    'sucesso': True,
                    'item': {
                        'id': nova_transp.id,
                        'razao_social': nova_transp.razao_social,
                        'cnpj': nova_transp.cnpj,
                        'cep': nova_transp.cep,
                        'endereco': nova_transp.endereco,
                        'numero': nova_transp.numero,
                        'bairro': nova_transp.bairro,
                        'cidade': nova_transp.cidade,
                        'estado': nova_transp.estado,
                        'nome_contato': nova_transp.nome_contato,
                        'email': nova_transp.email,
                        'telefone': nova_transp.telefone
                    }
                })

    transportadoras_list = Transportadora.query.all()
    return render_template('cadastros/transportadoras.html', transportadoras=transportadoras_list, erro=erro)


# --- FORNECEDORES ---
@cadastros_bp.route('/fornecedores', methods=['GET', 'POST'], strict_slashes=False)
def fornecedores():
    erro = None
    if request.method == 'POST':
        cnpj_limpo = apenas_numeros(request.form.get('cnpj'))
        forn_existente = Fornecedor.query.filter_by(cnpj=cnpj_limpo).first()
        
        if forn_existente:
            erro = "Fornecedor com este CNPJ já está cadastrado no sistema!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'sucesso': False, 'erro': erro}), 400
        else:
            novo_forn = Fornecedor(
                razao_social=request.form.get('razao_social'),
                cnpj=cnpj_limpo,
                cep=apenas_numeros(request.form.get('cep')),
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

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({
                    'sucesso': True,
                    'item': {
                        'id': novo_forn.id,
                        'razao_social': novo_forn.razao_social,
                        'cnpj': novo_forn.cnpj,
                        'cep': novo_forn.cep,
                        'endereco': novo_forn.endereco,
                        'numero': novo_forn.numero,
                        'bairro': novo_forn.bairro,
                        'cidade': novo_forn.cidade,
                        'estado': novo_forn.estado,
                        'nome_contato': novo_forn.nome_contato,
                        'email': novo_forn.email,
                        'telefone': novo_forn.telefone
                    }
                })

    fornecedores_list = Fornecedor.query.all()
    return render_template('cadastros/fornecedores.html', fornecedores=fornecedores_list, erro=erro)