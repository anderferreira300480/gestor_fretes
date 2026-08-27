from flask_sqlalchemy import SQLAlchemy

# Cria a instância do banco sem vinculá-la ao app ainda (evita importação circular)
db = SQLAlchemy()