import os
import pandas as pd
import numpy as np
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials
from fastapi import FastAPI
from telegram import Bot
from datetime import datetime

# ✅ Initialisation FastAPI
app = FastAPI()

# ✅ Variables d'environnement
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_CREDS_PATH = "/etc/secrets/credentials.json"
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# ✅ Fonction : Envoi Telegram
def send_telegram(message: str):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Erreur d'envoi Telegram : {e}")

# ✅ Fonction : Récupération des tickers depuis Google Sheets
def get_tickers_from_sheet():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds = Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        tickers = sheet.col_values(1)[1:]
        return [t.strip().upper() for t in tickers if t.strip()]
    except Exception as e:
        send_telegram(f"❌ Erreur lecture Google Sheets : {e}")
        return []

# ✅ Fonction : Analyse Ichimoku + Volatilité
def analyse_signaux():
    tickers = get_tickers_from_sheet()
    messages = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="3mo", interval="1d")
            if df.empty or len(df) < 52:
                continue

            df["tenkan"] = (df['High'].rolling(9).max() + df['Low'].rolling(9).min()) / 2
            df["kijun"] = (df['High'].rolling(26).max() + df['Low'].rolling(26).min()) / 2
            df["volatilite"] = df['Close'].rolling(10).std()

            last = df.iloc[-1]
            message = f"📈 {ticker} :"

            message += " Tenkan > Kijun ✅" if last['tenkan'] > last['kijun'] else " Tenkan < Kijun ❌"
            message += " | Close > Kijun ✅" if last['Close'] > last['kijun'] else " | Close < Kijun ❌"
            message += f" | Volatilité : {last['volatilite']:.2f}"

            messages.append(message)

        except Exception as e:
            messages.append(f"⚠️ {ticker} : erreur {str(e)}")

    if messages:
        send_telegram("🧠 Résumé analyse boursière :\n\n" + "\n".join(messages))
    else:
        send_telegram("🚫 Aucun signal détecté aujourd'hui.")

# ✅ Endpoint principal
@app.get("/")
def root():
    try:
        analyse_signaux()
        return {
            "status": "Analyse lancée",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {
            "status": "Erreur lors de l’analyse",
            "error": str(e)
        }
