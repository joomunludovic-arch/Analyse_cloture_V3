from fastapi import FastAPI
import yfinance as yf
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import numpy as np
from telegram import Bot
from datetime import datetime, timedelta

app = FastAPI()

# 🔐 Variables d’environnement
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDS_JSON = os.environ["GOOGLE_CREDS_JSON"]

# 📈 Connexion Google Sheets
def get_tickers_from_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = json.loads(GOOGLE_CREDS_JSON)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds, scope)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    tickers = sheet.col_values(1)
    return [ticker.strip() for ticker in tickers if ticker.strip()]

# 📊 Analyse Ichimoku + volatilité
def analyze_ticker(ticker):
    df = yf.download(ticker, period="3mo", interval="1d")
    if df.empty or len(df) < 52:
        return None

    df['tenkan'] = (df['High'].rolling(window=9).max() + df['Low'].rolling(window=9).min()) / 2
    df['kijun'] = (df['High'].rolling(window=26).max() + df['Low'].rolling(window=26).min()) / 2
    df['senkou_span_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)
    df['senkou_span_b'] = ((df['High'].rolling(window=52).max() + df['Low'].rolling(window=52).min()) / 2).shift(26)

    close = df['Close'].iloc[-1]
    tenkan = df['tenkan'].iloc[-1]
    kijun = df['kijun'].iloc[-1]
    span_a = df['senkou_span_a'].iloc[-1]
    span_b = df['senkou_span_b'].iloc[-1]

    signal_ichimoku = close > tenkan > kijun and close > span_a and close > span_b

    df['returns'] = df['Close'].pct_change()
    volatility = df['returns'].rolling(window=10).std().iloc[-1]

    signal_volatility = volatility > 0.02

    if signal_ichimoku or signal_volatility:
        return {
            "ticker": ticker,
            "close": round(close, 2),
            "volatility": round(volatility, 4),
            "signal_ichimoku": signal_ichimoku,
            "signal_volatility": signal_volatility,
        }
    return None

# 📬 Envoi Telegram
def send_telegram_message(text):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=text)

# ✅ Endpoint d’analyse
@app.get("/")
def run_analysis():
    try:
        tickers = get_tickers_from_google_sheet()
        messages = []
        for ticker in tickers:
            result = analyze_ticker(ticker)
            if result:
                msg = f"🔔 {result['ticker']}\nClôture: {result['close']}€\nVolatilité: {result['volatility']}\nIchimoku: {'✅' if result['signal_ichimoku'] else '❌'}\nVolatilité > 2%: {'✅' if result['signal_volatility'] else '❌'}"
                messages.append(msg)

        if messages:
            final_message = "📊 *Analyse Clôture du jour* 📈\n\n" + "\n\n".join(messages)
        else:
            final_message = "📊 Aucun signal détecté aujourd’hui."

        send_telegram_message(final_message)
        return {"status": "OK", "message": final_message}
    
    except Exception as e:
        error_msg = f"❌ Erreur: {str(e)}"
        send_telegram_message(error_msg)
        return {"status": "error", "message": error_msg}
