from app import create_app
from app.database import db
from app.models import Fornecedor

app = create_app()

with app.app_context():
    # Recria as tabelas para aplicar a nova estrutura com FK de fornecedor
    db.drop_all()
    db.create_all()

    f1 = Fornecedor(razao_social="Indústria de Aço Brasil S.A.", cnpj="33.444.555/0001-99")
    f2 = Fornecedor(razao_social="Distribuidora de Suprimentos LTDA", cnpj="66.777.888/0001-22")
    
    db.session.add_all([f1, f2])
    db.session.commit()
    print("Banco atualizado e Fornecedores cadastrados com sucesso!")