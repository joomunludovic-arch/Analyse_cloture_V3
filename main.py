import os
import json
import asyncio
from fastapi import FastAPI
from telegram import Bot
from telegram.constants import ParseMode
from google.oauth2.service_account import Credentials
import gspread
import yfinance as yf

app = FastAPI()

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
GOOGLE_SHEET_ID = os.environ['GOOGLE_SHEET_ID']

# Chemin vers le secret Render
GOOGLE_CREDS_PATH = "/etc/secrets/credentials.json"

def load_sheet_data():
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID)
    tickers = sheet.sheet1.col_values(1)[1:]  # Ignore l'en-tête
    return tickers

def analyse_ticker(ticker):
    try:
        data = yf.download(ticker, period="6mo", interval="1d")
        if data.empty or len(data) < 52:
            return f"{ticker} : Pas assez de données."

        closes = data["Close"]
        volatility = closes.pct_change().rolling(20).std().iloc[-1]

        nine_period_high = data['High'].rolling(window=9).max()
        nine_period_low = data['Low'].rolling(window=9).min()
        tenkan_sen = (nine_period_high + nine_period_low) / 2

        period26_high = data['High'].rolling(window=26).max()
        period26_low = data['Low'].rolling(window=26).min()
        kijun_sen = (period26_high + period26_low) / 2

        signal = "⚠️ Aucun signal détecté"
        if tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]:
            signal = f"✅ Signal haussier détecté sur {ticker}"
        elif tenkan_sen.iloc[-1] < kijun_sen.iloc[-1]:
            signal = f"🔻 Signal baissier détecté sur {ticker}"

        return f"{ticker} - Volatilité: {volatility:.4f} - {signal}"

    except Exception as e:
        return f"{ticker} : Erreur → {e}"

async def send_telegram_message(message: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)

@app.get("/")
async def run_analysis():
    tickers = load_sheet_data()
    results = [analyse_ticker(t) for t in tickers]
    message = "📊 <b>Analyse quotidienne</b>\n\n" + "\n".join(results)
    await send_telegram_message(message)
    return {"status": "ok", "message": "Analyse envoyée"}
