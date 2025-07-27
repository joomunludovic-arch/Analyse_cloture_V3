import os
import json
import pandas as pd
import yfinance as yf
import gspread
from fastapi import FastAPI
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot
from datetime import datetime, timedelta

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDS_PATH = "/etc/secrets/credentials.json"

app = FastAPI()

def load_tickers():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_PATH, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    return sheet.col_values(1)[1:]  # ignore header

def ichimoku_analysis(df):
    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    tenkan_sen = (high_9 + low_9) / 2
    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    kijun_sen = (high_26 + low_26) / 2
    return tenkan_sen, kijun_sen

def volatility_analysis(df):
    df['Return'] = df['Close'].pct_change()
    return df['Return'].std()

def send_telegram(message: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)

def analyse_ticker(ticker):
    try:
        df = yf.download(ticker, period="3mo", interval="1d")
        if df.empty:
            return

        tenkan, kijun = ichimoku_analysis(df)
        vol = volatility_analysis(df)

        last_close = df['Close'].iloc[-1]
        last_tenkan = tenkan.iloc[-1]
        last_kijun = kijun.iloc[-1]

        if last_close > last_tenkan > last_kijun and vol > 0.02:
            message = f"🔔 Signal sur {ticker}\nClôture: {last_close:.2f}\nVolatilité: {vol:.2%}"
            send_telegram(message)

    except Exception as e:
        print(f"Erreur pour {ticker}: {e}")

@app.get("/")
def run_analysis():
    tickers = load_tickers()
    for ticker in tickers:
        analyse_ticker(ticker)
    return {"status": "Analyse terminée", "tickers analysés": len(tickers)}
