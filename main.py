import os
from fastapi import FastAPI
from telegram import Bot
import yfinance as yf
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = FastAPI()

# 📌 Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# 📌 Google Sheets
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("/etc/secrets/credentials.json", scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1

# 📌 Fonction d’analyse Ichimoku + volatilité
def analyse_titre(ticker):
    data = yf.download(ticker, period="2mo", interval="1d")
    if data.empty:
        return None

    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    tenkan_sen = (high_9 + low_9) / 2

    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    kijun_sen = (high_26 + low_26) / 2

    current_price = data["Close"].iloc[-1]
    signal = ""

    if tenkan_sen.iloc[-1] > kijun_sen.iloc[-1] and current_price > tenkan_sen.iloc[-1]:
        signal = "Signal Haussier"
    elif tenkan_sen.iloc[-1] < kijun_sen.iloc[-1] and current_price < tenkan_sen.iloc[-1]:
        signal = "Signal Baissier"

    return f"{ticker} : {signal} - Clôture = {round(current_price, 2)}"

# 📌 Endpoint public déclenché par Google Script
@app.get("/")
def analyse():
    tickers = sheet.col_values(1)
    messages = []

    for ticker in tickers:
        result = analyse_titre(ticker)
        if result:
            messages.append(result)

    if messages:
        bot.send_message(chat_id=CHAT_ID, text="\n".join(messages))
        return {"status": "Messages envoyés"}
    else:
        return {"status": "Aucun signal détecté"}
