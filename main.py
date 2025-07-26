import os
from flask import Flask
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

def send_telegram_photo(photo_path, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})

def get_tickers_from_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    return sheet.col_values(1)[1:]  # Ignore la 1ère ligne (en-tête)

def get_ichimoku_signals(ticker):
    import yfinance as yf
    df = yf.download(ticker, period="3mo", interval="1d")
    if df.empty:
        return None, None

    df["tenkan_sen"] = (df["High"].rolling(window=9).max() + df["Low"].rolling(window=9).min()) / 2
    df["kijun_sen"] = (df["High"].rolling(window=26).max() + df["Low"].rolling(window=26).min()) / 2
    df["volatility"] = df["Close"].rolling(window=10).std()

    last = df.iloc[-1]
    signal = ""
    if last["Close"] > last["tenkan_sen"] and last["Close"] > last["kijun_sen"]:
        signal = "📈 Signal haussier"
    elif last["Close"] < last["tenkan_sen"] and last["Close"] < last["kijun_sen"]:
        signal = "📉 Signal baissier"

    # Graphique
    plt.figure(figsize=(10, 4))
    df["Close"].plot(label="Close")
    df["tenkan_sen"].plot(label="Tenkan-sen")
    df["kijun_sen"].plot(label="Kijun-sen")
    plt.legend()
    plt.title(ticker)
    chart_path = f"{ticker}.png"
    plt.savefig(chart_path)
    plt.close()

    return signal, chart_path

@app.route('/')
def analyse():
    try:
        tickers = get_tickers_from_sheet()
        alerts = []

        for ticker in tickers:
            signal, image = get_ichimoku_signals(ticker)
            if signal:
                alerts.append(f"{ticker} : {signal}")
                send_telegram_photo(image, f"{ticker} : {signal}")

        if alerts:
            send_telegram_message("📊 Alertes détectées :\n\n" + "\n".join(alerts))
        else:
            send_telegram_message("✅ Aucune alerte aujourd’hui.")
        return "✅ Analyse terminée avec succès"
    except Exception as e:
        send_telegram_message(f"❌ Erreur : {str(e)}")
        return f"❌ Erreur : {str(e)}"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
