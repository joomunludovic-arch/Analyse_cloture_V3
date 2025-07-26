from flask import Flask
from analyseur import analyser_et_envoyer

app = Flask(__name__)

@app.route('/')
def trigger():
    try:
        message = analyser_et_envoyer()
        return f"✅ Script exécuté avec succès : {message}", 200
    except Exception as e:
        return f"❌ Erreur dans le script : {str(e)}", 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
