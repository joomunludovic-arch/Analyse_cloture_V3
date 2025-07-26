import os
import pandas as pd
import numpy as np
import yfinance as yf
import gspread
from fastapi import FastAPI
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot
from datetime import datetime

# Initialisation FastAPI
app = FastAPI()

# Variables d'environnement
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_CREDS_PATH = "/etc/secrets/credentials.json"
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# Fonction : Envoi Telegram
def send_telegram(message: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)

# Fonction : Récupération des tickers depuis Google Sheets
def get_tickers_from_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_PATH, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    tickers = sheet.col_values(1)[1:]  # ignore l'entête
    return [t.strip().upper() for t in tickers if t.strip()]

# Fonction : Analyse Ichimoku
def analyse_ichimoku(df):
    nine_period_high = df['High'].rolling(window=9).max()
    nine_period_low = df['Low'].rolling(window=9).min()
    df['tenkan_sen'] = (nine_period_high + nine_period_low) / 2

    period26_high = df['High'].rolling(window=26).max()
    period26_low = df['Low'].rolling(window=26).min()
    df['kijun_sen'] = (period26_high + period26_low) / 2

    df['signal_ichimoku'] = np.where(df['tenkan_sen'] > df['kijun_sen'], "achat", "vente")
    return df

# Fonction : Analyse Volatilité
def analyse_volatilite(df):
    df['returns'] = df['Close'].pct_change()
    df['volatility'] = df['returns'].rolling(window=10).std()
    return df

# Fonction principale : Analyse complète
def analyse_titres():
    tickers = get_tickers_from_sheet()
    messages = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="3mo", interval="1d")
            if df.empty:
                continue

            df = analyse_ichimoku(df)
            df = analyse_volatilite(df)

            dernier_signal = df.iloc[-1]
            ichimoku = dernier_signal['signal_ichimoku']
            volatilite = round(dernier_signal['volatility'] * 100, 2)

            message = f"🔔 {ticker}\n📊 Signal Ichimoku : {ichimoku.upper()}\n📈 Volatilité (10j) : {volatilite} %"
            messages.append(message)

        except Exception as e:
            messages.append(f"Erreur pour {ticker} : {e}")

    for msg in messages:
        send_telegram(msg)

# Route FastAPI
@app.get("/")
def trigger_script():
    try:
        analyse_titres()
        return {"status": "OK", "message": "Analyse terminée et envoyée sur Telegram."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
