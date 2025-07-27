import os
import json
import yfinance as yf
import pandas as pd
import gspread
from fastapi import FastAPI
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot

app = FastAPI()

# ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

bot = Bot(token=TELEGRAM_TOKEN)

@app.get("/")
def analyse():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(GOOGLE_CREDS_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        tickers = sheet.col_values(1)[1:]

        message = ""
        for ticker in tickers:
            data = yf.download(ticker, period="30d", interval="1d")
            if data.empty:
                continue

            # VOLATILITÉ
            data['Volatility'] = data['High'] - data['Low']
            mean_vol = data['Volatility'].mean()

            # ICHIMOKU
            nine_period_high = data['High'].rolling(window=9).max()
            nine_period_low = data['Low'].rolling(window=9).min()
            data['tenkan_sen'] = (nine_period_high + nine_period_low) / 2

            twenty_six_high = data['High'].rolling(window=26).max()
            twenty_six_low = data['Low'].rolling(window=26).min()
            data['kijun_sen'] = (twenty_six_high + twenty_six_low) / 2

            tenkan = data['tenkan_sen'].iloc[-1]
            kijun = data['kijun_sen'].iloc[-1]
            close = data['Close'].iloc[-1]

            if tenkan > kijun and close > kijun:
                message += f"🔔 Signal HAUSSIER détecté sur {ticker} (Volatilité moy: {mean_vol:.2f})\n"

        if message:
            bot.send_message(chat_id=CHAT_ID, text=message)
            return {"status": "Signal envoyé", "message": message}
        else:
            return {"status": "Aucun signal détecté"}

    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"Erreur détectée: {e}")
        return {"status": "Erreur", "details": str(e)}
