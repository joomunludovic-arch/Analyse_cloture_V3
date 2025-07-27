import os
import pandas as pd
import numpy as np
import yfinance as yf
import gspread
from fastapi import FastAPI
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot
from datetime import datetime

app = FastAPI()

# 🔐 Variables d'environnement
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDS_PATH = "/etc/secrets/credentials.json"

# ✅ Fonction d’envoi Telegram
def send_telegram(message: str):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"[ERROR] Telegram: {e}")

# ✅ Récupération des tickers depuis Google Sheets
def get_tickers_from_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_PATH, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    tickers = sheet.col_values(1)[1:]
    return [t.strip().upper() for t in tickers if t.strip()]

# ✅ Analyse Ichimoku + Volatilité
def analyse_signaux():
    tickers = get_tickers_from_sheet()
    messages = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="3mo", interval="1d")
            if df.empty or len(df) < 52:
                messages.append(f"⚠️ {ticker} : données insuffisantes.")
                continue

            df["tenkan"] = (df['High'].rolling(9).max() + df['Low'].rolling(9).min()) / 2
            df["kijun"] = (df['High'].rolling(26).max() + df['Low'].rolling(26).min()) / 2
            df["volatilite"] = df['Close'].rolling(10).std()

            last = df.iloc[-1]
            message = f"📈 {ticker} :"

            message += " Tenkan > Kijun ✅" if last["tenkan"] > last["kijun"] else " Tenkan < Kijun ❌"
            message += " | Close > Kijun ✅" if last["Close"] > last["kijun"] else " | Close < Kijun ❌"
            message += f" | Volatilité : {last['volatilite']:.2f}"

            messages.append(message)

        except Exception as e:
            messages.append(f"⚠️ {ticker} : erreur {str(e)}")

    final_message = "🧠 Résumé analyse boursière :\n\n" + "\n".join(messages) if messages else "🚫 Aucun signal détecté."
    send_telegram(final_message)

# ✅ Endpoint HTTP pour déclencher l’analyse
@app.get("/")
def run():
    analyse_signaux()
    return {"status": "Analyse lancée", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
