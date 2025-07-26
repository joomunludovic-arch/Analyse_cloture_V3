from flask import Flask
import asyncio
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials
from telegram import Bot
import os

# Initialisation Flask
app = Flask(__name__)

# Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# Google Sheets
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
GOOGLE_CREDS_JSON = "/etc/secrets/credentials.json"

SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(GOOGLE_CREDS_JSON, scopes=SCOPES)
client = gspread.authorize(creds)

# Fonction analyse
def analyse():
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    tickers = sheet.col_values(1)[1:]  # Ignore l'en-tête
    messages = []

    for ticker in tickers:
        data = yf.download(ticker, period="2d", interval="1d")
        if data.empty or len(data) < 2:
            continue

        yesterday_close = data["Close"].iloc[-2]
        today_close = data["Close"].iloc[-1]
        variation = ((today_close - yesterday_close) / yesterday_close) * 100

        if abs(variation) > 3:
            messages.append(f"{ticker}: variation de {variation:.2f}%")

    if messages:
        return "\n".join(messages)
    else:
        return "Aucune variation significative détectée."

# Route principale
@app.route("/")
def index():
    result = analyse()
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text=result))
    return "Analyse envoyée sur Telegram ✅"

if __name__ == "__main__":
    app.run(debug=True)
