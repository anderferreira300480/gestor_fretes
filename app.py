from flask import Flask

app == Flask(__name__)

@app.route("/")
def home():
    return "<h1>Sistema de Gestão de Fretes no ar!</h1>"

if __name__ == "__main__":
    app.run(debug-True)