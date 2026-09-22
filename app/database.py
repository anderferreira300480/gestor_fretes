"""Ponto único de criação da extensão de banco de dados."""

from flask_sqlalchemy import SQLAlchemy

# A extensão é criada sem app e recebe o app em create_app(). Esse padrão
# permite importar os modelos sem criar uma aplicação global antecipadamente.
db = SQLAlchemy()