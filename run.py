"""Ponto de entrada usado para executar o servidor Flask local."""

from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True habilita recarga automática e páginas de erro detalhadas;
    # deve ser desligado em qualquer ambiente exposto à rede.
    app.run(debug=True)