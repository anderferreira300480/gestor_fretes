from flask import Blueprint, render_template, request, redirect, url_for
from app.database import db
from app.models import Pedido, CotacaoFrete, Transportadora

cotacoes_bp = Blueprint('cotacoes', __name__)

@cotacoes_bp.route('/cotacoes/adicionar/<int:pedido_id>', methods=['POST'])
def adicionar(pedido_id):
    transportadora_id = request.form.get('transportadora_id')
    valor_frete = request.form.get('valor_cotado')  # Pega do campo do form
    prazo_dias = request.form.get('prazo_dias')

    if transportadora_id and valor_frete and prazo_dias:
        nova_cotacao = CotacaoFrete(
            pedido_id=pedido_id,
            transportadora_id=int(transportadora_id),
            valor_frete=float(valor_frete),
            prazo_dias=int(prazo_dias)
        )
        db.session.add(nova_cotacao)
        db.session.commit()

    pedido = Pedido.query.get_or_404(pedido_id)
    transportadoras = Transportadora.query.all()
    
    # Retorna o fragmento do detalhes.html atualizado
    return render_template('pedidos/detalhes.html', pedido=pedido, transportadoras=transportadoras)


@cotacoes_bp.route('/cotacoes/<int:cotacao_id>/selecionar-vencedor', methods=['POST'])
def selecionar_vencedor(cotacao_id):
    cotacao = CotacaoFrete.query.get_or_404(cotacao_id)
    
    # Desmarca outras cotações do mesmo pedido e marca a escolhida
    CotacaoFrete.query.filter_by(pedido_id=cotacao.pedido_id).update({'vencedora': False})
    cotacao.vencedora = True
    
    # Atualiza o status do pedido
    cotacao.pedido.status = 'Aguardando Coleta'
    db.session.commit()

    pedido = Pedido.query.get_or_404(cotacao.pedido_id)
    transportadoras = Transportadora.query.all()
    
    return render_template('pedidos/detalhes.html', pedido=pedido, transportadoras=transportadoras)