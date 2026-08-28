from app import create_app
from app.database import db
from app.models import Empresa, Transportadora, Fornecedor

app = create_app()

with app.app_context():
    # Recria a estrutura do banco com as novas colunas
    db.drop_all()
    db.create_all()

    # EMPRESAS (COMPRADORAS)
    e1 = Empresa(
        razao_social="Copelmi Mineração LTDA - Butiá", cnpj="33.059.528/0003-57",
        endereco="Br.290, Km 178", numero="S/N", bairro="Santo Antônio", cidade="Butiá", estado="RS",
        nome_contato="Anderson", email="anderson@copelmi.com.br", telefone="(51)998063568"
    )
    e2 = Empresa(
        razao_social="Copelmi Mineração LTDA - Cachoeira do Sul", cnpj="33.059.528/0013-29",
        endereco="Est. Cerro Manoel Prates, Km 16", bairro="Capané", numero="S/N", cidade="Cachoeira do Sul", estado="RS",
        nome_contato="Anderson", email="anderson@copelmi.com.br", telefone="(51)998063568"
    )

    # FORNECEDORES
    f1 = Fornecedor(
        razao_social="Soldasul Indústria Comércio e Improtação LTDA", cnpj="87.020.756/0002-61",
        endereco="Av. Paraná", numero="1499", bairro="São Geraldo", cidade="Porto Alegre", estado="RS",
        nome_contato="Lucimara", email="lucimra@soldasul.com.br", telefone="(51)991970215"
    )
    f2 = Fornecedor(
        razao_social="Steelrool Indústria Metalúrgica LTDA", cnpj="09.515.037/0001-27",
        endereco="Rod. Otávio Dassoler", numero="4490", bairro="Linha Batista", cidade="Criciúma", estado="SC",
        nome_contato="Ismael Schinato", email="vendas@steerool.com.br", telefone="(48)996170249"
    )

    # TRANSPORTADORAS
    t1 = Transportadora(
        razao_social="Transportes Raccontare LTDA", cnpj="06.063.517/0002-97",
        endereco="Av. Carlos Gomes", numero="1672", bairro="Três Figueiras", cidade="Porto Alegre", estado="RS",
        nome_contato="Nayane Cardoso", email="comercial03@ili.log.br", telefone="(51)999287309"
    )
    t2 = Transportadora(
        razao_social="Transportadora Sordi - TS Log", cnpj="17.290.964/0001-14",
        endereco="Av Obedy Cândido Vieira-C", numero="801", bairro="Central Park", cidade="Chachoeirinha", estado="RS",
        nome_contato="Maicon Sordi", email="maicon.sordi@transordi.com.br", telefone="(51)992873226 "
    )

    db.session.add_all([e1, e2, f1, f2, t1, t2])
    db.session.commit()
    print("Banco de dados resetado e atualizado com endereços e dados de contato!")