import yfinance as yf
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import requests
from datetime import datetime, timedelta

def send_telegram_message(message):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def analyser_et_envoyer():
    sheet_id = os.environ['GOOGLE_SHEET_ID']
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1
    tickers = sheet.col_values(1)[1:]  # Ignore header

    messages = []
    for ticker in tickers:
        data = yf.download(ticker, period="3mo", interval="1d")
        if data.empty or len(data) < 52:
            continue

        # Ichimoku
        nine_high = data['High'].rolling(window=9).max()
        nine_low = data['Low'].rolling(window=9).min()
        data['tenkan_sen'] = (nine_high + nine_low) / 2
        data['kijun_sen'] = (data['High'].rolling(window=26).max() + data['Low'].rolling(window=26).min()) / 2

        # Volatility
        data['returns'] = data['Close'].pct_change()
        data['volatility'] = data['returns'].rolling(window=14).std()

        latest = data.iloc[-1]
        if latest['tenkan_sen'] > latest['kijun_sen'] and latest['volatility'] > 0.02:
            messages.append(f"🔔 Signal détecté sur {ticker} (Tendance haussière + forte volatilité)")

    final_msg = "\n".join(messages) if messages else "✅ Aucun signal détecté aujourd'hui."
    send_telegram_message(final_msg)
    return final_msg
