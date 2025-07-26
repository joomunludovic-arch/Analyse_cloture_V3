import os
import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from flask import Flask

# 📌 Initialisation Flask
app = Flask(__name__)

# 🔐 Clés d’environnement (à définir sur Render → Settings → Environment)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# 📤 Envoi Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# 📊 Lecture tickers depuis Google Sheets
def get_tickers_from_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    tickers = sheet.col_values(1)
    return [t.strip().upper() for t in tickers if t.strip()]

# 🧠 Ichimoku
def calculate_ichimoku(df):
    df['tenkan_sen'] = (df['High'].rolling(9).max() + df['Low'].rolling(9).min()) / 2
    df['kijun_sen'] = (df['High'].rolling(26).max() + df['Low'].rolling(26).min()) / 2
    return df

# 🚀 Analyse globale
@app.route('/')
def run_analysis():
    try:
        tickers = get_tickers_from_google_sheet()
        all_signals = []

        for ticker in tickers:
            df = yf.download(ticker, period="3mo", interval="1d")
            if df.empty:
                continue

            df.reset_index(inplace=True)
            df['Volatility'] = df['Close'].rolling(window=10).std()
            vol_mean = df['Volatility'].mean()
            vol_std = df['Volatility'].std()
            df['Z_score'] = (df['Volatility'] - vol_mean) / vol_std
            df = calculate_ichimoku(df)

            df['Signal'] = np.where(
                (df['Z_score'] > 2) & (df['Close'] > df['tenkan_sen']) & (df['Close'] > df['kijun_sen']),
                "📈 Signal haussier",
                np.where(
                    (df['Z_score'] > 2) & (df['Close'] < df['tenkan_sen']) & (df['Close'] < df['kijun_sen']),
                    "📉 Signal baissier",
                    ""
                )
            )

            signals = df[df['Signal'] != ""][['Date', 'Close', 'Z_score', 'Signal']].tail(3)
            for _, row in signals.iterrows():
                msg = (
                    f"📌 {ticker} - {row['Date'].strftime('%Y-%m-%d')}\n"
                    f"💰 {row['Close']:.2f} | Z = {row['Z_score']:.2f}\n"
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
        return f"❌ Erreur dans le script : {str(e)}"

# 🔁 Lancement local (optionnel, utile pour tests hors Render)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
