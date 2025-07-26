import os
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import matplotlib.pyplot as plt
import gspread
import yfinance as yf
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask
from analyseur import analyser_et_envoyer

app = Flask(__name__)

@app.route('/')
def home():
    resultat = analyser_et_envoyer()
    return f"✅ Analyse terminée : {resultat}", 200

# ENV VARIABLES
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_CREDENTIALS_JSON = "/etc/secrets/secret.json"
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Erreur Telegram : {e}")
