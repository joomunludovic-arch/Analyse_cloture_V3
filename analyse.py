import yfinance as yf
import pandas as pd
import datetime
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

def analyser_et_envoyer():
    # Authentification Google Sheets
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("secret.json", scope)
    client = gspread.authorize(creds)
    
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    sheet = client.open_by_key(sheet_id).sheet1
    tickers = sheet.col_values(1)[1:]

    messages = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="6mo", interval="1d")
            if df.empty:
                continue

            # Ichimoku
            nine_period_high = df['High'].rolling(window=9).max()
            nine_period_low = df['Low'].rolling(window=9).min()
            df['tenkan_sen'] = (nine_period_high + nine_period_low) / 2

            period26_high = df['High'].rolling(window=26).max()
            period26_low = df['Low'].rolling(window=26).min()
            df['kijun_sen'] = (period26_high + period26_low) / 2

            df['signal'] = df['tenkan_sen'] > df['kijun_sen']

            # Volatilité
            df['returns'] = df['Close'].pct_change()
            volatility = df['returns'].rolling(window=14).std().iloc[-1]

            # Conditions
            if df['signal'].iloc[-1] and volatility > 0.02:
                messages.append(f"📈 {ticker} : Signal Ichimoku + forte volatilité")

        except Exception as e:
            messages.append(f"❌ Erreur sur {ticker} : {e}")

    if messages:
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        final_message = "\n".join(messages)
        requests.get(f"https://api.telegram.org/bot{token}/sendMessage", params={
            "chat_id": chat_id,
            "text": final_message
        })
