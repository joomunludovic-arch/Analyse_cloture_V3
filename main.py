from flask import Flask
import yfinance as yf
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import requests

app = Flask(__name__)

# --- Configuration ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# --- Authentification Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(credentials)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, data=data)
    return response.status_code

def analyse_action(ticker):
    try:
        now = datetime.datetime.now()
        start = now - datetime.timedelta(days=90)
        df = yf.download(ticker, start=start, end=now)

        if df.empty or len(df) < 52:
            return f"{ticker} : données insuffisantes"

        # Ichimoku - simplifié
        nine_high = df['High'].rolling(window=9).max()
        nine_low = df['Low'].rolling(window=9).min()
        df['tenkan_sen'] = (nine_high + nine_low) / 2

        twenty_six_high = df['High'].rolling(window=26).max()
        twenty_six_low = df['Low'].rolling(window=26).min()
        df['kijun_sen'] = (twenty_six_high + twenty_six_low) / 2

        last_row = df.iloc[-1]
        tenkan = last_row['tenkan_sen']
        kijun = last_row['kijun_sen']
        close = last_row['Close']

        ichimoku_signal = "🟢 Achat" if close > tenkan > kijun else "🔴 Vente"

        # Volatilité
        df['Volatility'] = df['Close'].pct_change().rolling(window=10).std()
        vol = df['Volatility'].iloc[-1]
        vol_signal = "📈 Volatilité haute" if vol > 0.02 else "📉 Volatilité basse"

        return f"{ticker} : {ichimoku_signal} | {vol_signal}"
    except Exception as e:
        return f"{ticker} : erreur - {str(e)}"

@app.route('/')
def index():
    try:
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        tickers = sheet.col_values(1)[1:]  # Ignore l'en-tête
        messages = [analyse_action(ticker.strip()) for ticker in tickers if ticker.strip()]
        final_message = "\n".join(messages)
        send_telegram_message(final_message)
        return "✅ Analyse exécutée avec succès"
    except Exception as e:
        return f"❌ Erreur : {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
