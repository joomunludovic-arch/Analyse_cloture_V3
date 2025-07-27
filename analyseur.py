import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import yfinance as yf
import pandas as pd
from telegram import Bot
from datetime import datetime

def run():
    try:
        # Initialisation des variables d’environnement
        GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
        TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
        CHAT_ID = os.environ.get("CHAT_ID")

        # Connexion Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_path = "/etc/secrets/credentials.json"
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        tickers = sheet.col_values(1)[1:]  # ignorer l’en-tête

        # Initialisation Telegram
        bot = Bot(token=TELEGRAM_TOKEN)

        messages = []

        for ticker in tickers:
            data = yf.download(ticker, period="1mo", interval="1d")
            if data.empty or len(data) < 30:
                continue

            # VOLATILITÉ (écart-type sur 20 jours)
            volatility = data["Close"].pct_change().rolling(window=20).std().iloc[-1]

            # ICHIMOKU
            high_9 = data['High'].rolling(window=9).max()
            low_9 = data['Low'].rolling(window=9).min()
            tenkan_sen = (high_9 + low_9) / 2

            high_26 = data['High'].rolling(window=26).max()
            low_26 = data['Low'].rolling(window=26).min()
            kijun_sen = (high_26 + low_26) / 2

            if tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]:
                signal = "💹 Signal haussier"
            elif tenkan_sen.iloc[-1] < kijun_sen.iloc[-1]:
                signal = "📉 Signal baissier"
            else:
                signal = "⏸️ Pas de signal clair"

            message = f"{ticker} | {signal} | Volatilité: {volatility:.2%}"
            messages.append(message)

        # Envoi du message Telegram
        if messages:
            final_message = "\n".join(messages)
        else:
            final_message = "Aucun signal détecté aujourd'hui."

        bot.send_message(chat_id=CHAT_ID, text=final_message)

        return "Analyse envoyée avec succès."
    except Exception as e:
        return f"Erreur : {e}"
