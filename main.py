import os
import pandas as pd
import numpy as np
import yfinance as yf
import gspread
from fastapi import FastAPI
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot
from datetime import datetime
from fastapi.responses import JSONResponse

# Initialisation de l'app FastAPI
app = FastAPI()

# Variables d'environnement
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_CREDS_PATH = "/etc/secrets/credentials.json"
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# Envoi d'un message Telegram
def send_telegram(message: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)

# Récupération des tickers dans Google Sheets
def get_tickers_from_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_PATH, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    tickers = sheet.col_values(1)[1:]
    return [t.strip().upper() for t in tickers if t.strip()]

# Analyse Ichimoku + Volatilité
def analyse_signaux():
    tickers = get_tickers_from_sheet()
    messages = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="3mo", interval="1d")
            if df.empty or len(df) < 52:
                messages.append(f"⚠️ {ticker} : pas assez de données")
                continue

            df["tenkan"] = (df['High'].rolling(9).max() + df['Low'].rolling(9).min()) / 2
            df["kijun"] = (df['High'].rolling(26).max() + df['Low'].rolling(26).min()) / 2
            df["volatilite"] = df['Close'].rolling(10).std()

            last = df.iloc[-1]
            msg = f"📈 {ticker} :"

            msg += " Tenkan > Kijun ✅" if last['tenkan'] > last['kijun'] else " Tenkan < Kijun ❌"
            msg += " | Close > Kijun ✅" if last['Close'] > last['kijun'] else " | Close < Kijun ❌"
            msg += f" | Volatilité : {last['volatilite']:.2f}"

            messages.append(msg)

        except Exception as e:
            messages.append(f"⚠️ {ticker} : erreur {str(e)}")

    if messages:
        send_telegram("🧠 Résumé analyse boursière :\n\n" + "\n".join(messages))
    else:
        send_telegram("🚫 Aucun signal détecté aujourd'hui.")

# Endpoint HTTP pour ping Render ou Google Apps Script
@app.get("/")
def run():
    try:
        analyse_signaux()
        return JSONResponse(status_code=200, content={
            "status": "Analyse lancée",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "Erreur",
            "message": str(e)
        })
