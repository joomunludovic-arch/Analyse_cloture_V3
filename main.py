import os
import json
import logging
import yfinance as yf
import pandas as pd
from telegram import Bot
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from fastapi import FastAPI
import uvicorn

# Initialisation FastAPI
app = FastAPI()

# Configuration logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === VARIABLES D'ENVIRONNEMENT ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDS_JSON = os.environ["GOOGLE_CREDS_JSON"]

# === GOOGLE SHEETS ===
creds_dict = json.loads(GOOGLE_CREDS_JSON)
credentials = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
sheets_service = build("sheets", "v4", credentials=credentials)
sheet_range = "Feuille1!A:A"
result = sheets_service.spreadsheets().values().get(spreadsheetId=GOOGLE_SHEET_ID, range=sheet_range).execute()
tickers = [row[0] for row in result.get("values", []) if row]

# === TELEGRAM ===
bot = Bot(token=TELEGRAM_TOKEN)

def send_telegram(message: str):
    bot.send_message(chat_id=CHAT_ID, text=message)

# === ANALYSE ICHIMOKU & VOLATILITÉ ===
def analyze_stock(ticker):
    df = yf.download(ticker, period="3mo", interval="1d")
    if df.empty or len(df) < 52:
        return f"{ticker} - Pas assez de données"

    df["tenkan_sen"] = (df["High"].rolling(window=9).max() + df["Low"].rolling(window=9).min()) / 2
    df["kijun_sen"] = (df["High"].rolling(window=26).max() + df["Low"].rolling(window=26).min()) / 2
    df["volatilite"] = df["Close"].rolling(window=14).std()

    signal = ""
    if df["tenkan_sen"].iloc[-1] > df["kijun_sen"].iloc[-1]:
        signal += "🔼 Tenkan > Kijun ➜ Tendance haussière\n"
    else:
        signal += "🔽 Tenkan < Kijun ➜ Tendance baissière\n"

    volat = df["volatilite"].iloc[-1]
    signal += f"📊 Volatilité actuelle : {volat:.2f}"

    return f"📈 {ticker} :\n{signal}"

# === ENDPOINT TRIGGERABLE PAR APPEL HTTP (Render) ===
@app.get("/")
def run_analysis():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"📊 Analyse automatique du {now} :\n"
    messages = [header]

    for ticker in tickers:
        try:
            result = analyze_stock(ticker)
            messages.append(result)
        except Exception as e:
            messages.append(f"❌ Erreur pour {ticker} : {e}")

    full_message = "\n\n".join(messages)
    send_telegram(full_message)

    return {"status": "OK", "message": "Analyse envoyée sur Telegram ✅"}

# === POINT D'ENTRÉE LOCAL SI TEST EN DEV ===
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
