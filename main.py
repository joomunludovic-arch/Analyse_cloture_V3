from flask import Flask
import requests
import yfinance as yf
import pandas as pd
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")

@app.route('/')
def analyse():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv"
        tickers = pd.read_csv(url)['Ticker'].dropna().tolist()
        messages = []

        for ticker in tickers:
            data = yf.download(ticker, period="7d", interval="1d")
            if data.empty or len(data) < 2:
                continue

            close_prices = data["Close"]
            volatility = close_prices.pct_change().std()
            last_close = close_prices.iloc[-1]

            ichimoku_signal = "⚠️ Incertain"
            if last_close > close_prices.mean():
                ichimoku_signal = "📈 Signal haussier"
            elif last_close < close_prices.mean():
                ichimoku_signal = "📉 Signal baissier"

            messages.append(f"{ticker}: {ichimoku_signal} | 📊 Volatilité: {volatility:.2%}")

        final_message = "\n".join(messages)
        send_telegram(final_message or "Aucune donnée disponible.")
        return "OK", 200

    except Exception as e:
        send_telegram(f"❌ Erreur dans l'analyse : {str(e)}")
        return "Erreur", 500

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)
