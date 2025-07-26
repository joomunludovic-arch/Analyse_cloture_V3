from flask import Flask
from analyse import analyser_et_envoyer

app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Analyse clôture V3 OK"

@app.route('/analyse')
def analyse_route():
    analyser_et_envoyer()
    return "✅ Analyse exécutée"

if __name__ == '__main__':
    app.run()
