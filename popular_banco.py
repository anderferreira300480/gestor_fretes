from app import create_app
from app.database import db
from app.models import Empresa

app = create_app()

with app.app_context():
    # Verifica se já existem empresas cadastradas
    if not Empresa.query.first():
        e1 = Empresa(razao_social="Copelmi Mineração Ltda - Butiá", cnpj="33.059.528/0003-57")
        e2 = Empresa(razao_social="Copelmi Mineração Ltda - Cachoeira do Sul", cnpj="33.059.528/0013-29")
        
        db.session.add_all([e1, e2])
        db.session.commit()
        print("Empresas cadastradas com sucesso!")
    else:
        print("O banco já possui empresas cadastradas.")