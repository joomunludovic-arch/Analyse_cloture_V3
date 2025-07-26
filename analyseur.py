import os
import yfinance as yf
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from main import send_telegram_message

def analyser_et_envoyer():
    try:
        # Connexion Google Sheets
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name("/etc/secrets/secret.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1
        tickers = sheet.col_values(1)[1:]

        messages = []
        for ticker in tickers:
            data = yf.download(ticker, period="2mo", interval="1d")
            if len(data) < 52:
                continue

            # Volatilité simple
            data["returns"] = data["Close"].pct_change()
            volatility = np.std(data["returns"].dropna()) * 100

            # Ichimoku Kijun
            nine_period_high = data['High'].rolling(window=9).max()
            nine_period_low = data['Low'].rolling(window=9).min()
            data['tenkan_sen'] = (nine_period_high + nine_period_low) / 2
            data['kijun_sen'] = (data['High'].rolling(window=26).max() + data['Low'].rolling(window=26).min()) / 2

            last_close = data['Close'].iloc[-1]
            last_kijun = data['kijun_sen'].iloc[-1]
            last_tenkan = data['tenkan_sen'].iloc[-1]

            if last_close > last_kijun and last_tenkan > last_kijun:
                messages.append(f"🔔 {ticker} : Signal haussier 📈 (Volatilité : {volatility:.2f}%)")

        if messages:
            final_message = "\n".join(messages)
            send_telegram_message(final_message)
            return final_message
        else:
            return "Aucun signal détecté aujourd'hui."
    except Exception as e:
        send_telegram_message(f"❌ Erreur dans l’analyse : {e}")
        return f"Erreur dans l’analyse : {e}"
