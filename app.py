from flask import Flask
import main

app = Flask(__name__)

@app.route('/')
def index():
    main.main()
    return "Analyse exécutée avec succès"
