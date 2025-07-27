import os
import json
import yfinance as yf
import pandas as pd
import gspread
from fastapi import FastAPI
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot

app = FastAPI()

# 🔐 Variables d'environnement
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# 🔐 Accès Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(GOOGLE_CREDS_JSON)
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1

# 🔍 Analyse Ichimoku + Volatilité
def analyse_titre(ticker):
    data = yf.download(ticker, period="3mo", interval="1d")
    if data.empty:
        return f"❌ Aucune donnée pour {ticker}"
    
    # Ichimoku
    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    tenkan_sen = (high_9 + low_9) / 2

    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    kijun_sen = (high_26 + low_26) / 2

    close = data['Close']
    volatility = close.pct_change().rolling(window=5).std()[-1]

    last_price = close[-1]
    signal = ""

    if tenkan_sen[-1] > kijun_sen[-1] and close[-1] > tenkan_sen[-1]:
        signal = "📈 Signal haussier"
    elif tenkan_sen[-1] < kijun_sen[-1] and close[-1] < tenkan_sen[-1]:
        signal = "📉 Signal baissier"
    else:
        signal = "⏸️ Aucun signal clair"

    return f"{ticker} : {signal} | Volatilité : {volatility:.2%}"

# 🔔 Envoi Telegram
def send_telegram(message):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)

# ▶️ Endpoint d’analyse
@app.get("/")
def run_analysis():
    tickers = sheet.col_values(1)[1:]
    results = []

    for ticker in tickers:
        try:
            result = analyse_titre(ticker)
            results.append(result)
        except Exception as e:
            results.append(f"⚠️ Erreur sur {ticker} : {str(e)}")

    final_message = "\n".join(results)
    send_telegram(final_message)
    return {"status": "ok", "message": final_message}
