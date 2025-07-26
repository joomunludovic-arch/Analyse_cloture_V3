import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from flask import Flask
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Initialisation Flask
app = Flask(__name__)

# Variables d'environnement
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_JSON = "/etc/secrets/credentials.json"

# Connexion à Google Sheets
def get_tickers_from_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_JSON, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    tickers = sheet.col_values(1)
    return [t.strip().upper() for t in tickers if t.strip()]

# Fonction pour envoyer un message Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# Fonction principale
@app.route('/')
def run_analysis():
    try:
        tickers = get_tickers_from_sheets()
        all_signals = []

        for ticker in tickers:
            df = yf.download(ticker, period="3mo", interval="1d")
            if df.empty or 'Close' not in df:
                continue

            df['Volatility'] = df['Close'].rolling(window=10).std()
            vol_mean = df['Volatility'].mean()
            vol_std = df['Volatility'].std()
            df['Z_score'] = (df['Volatility'] - vol_mean) / vol_std

            df['Tenkan_sen'] = df['High'].rolling(window=9).max() + df['Low'].rolling(window=9).min()
            df['Tenkan_sen'] /= 2
            df['Kijun_sen'] = df['High'].rolling(window=26).max() + df['Low'].rolling(window=26).min()
            df['Kijun_sen'] /= 2

            df['Signal'] = np.where(
                (df['Z_score'] > 2) & (df['Close'] > df['Tenkan_sen']) & (df['Close'] > df['Kijun_sen']),
                "📈 Signal haussier",
                np.where(
                    (df['Z_score'] > 2) & (df['Close'] < df['Tenkan_sen']) & (df['Close'] < df['Kijun_sen']),
                    "📉 Signal baissier",
                    ""
                )
            )

            signals = df[df['Signal'] != ""].tail(3)[['Close', 'Z_score', 'Signal']]
            for idx, row in signals.iterrows():
                msg = (
                    f"📌 {ticker} - {idx.strftime('%Y-%m-%d')}\n"
                    f"💰 {row['Close']:.2f} | Z={row['Z_score']:.2f}\n"
                    f"{row['Signal']}"
                )
                all_signals.append(msg)

        if all_signals:
            send_telegram_message("📊 Signaux détectés :\n\n" + "\n\n".join(all_signals))
        else:
            send_telegram_message("✅ Aucune anomalie détectée aujourd’hui.")
        return "✅ Analyse exécutée avec succès"
    except Exception as e:
        send_telegram_message(f"❌ Erreur : {str(e)}")
        return f"❌ Erreur : {str(e)}"
