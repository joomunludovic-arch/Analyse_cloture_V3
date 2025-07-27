import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import yfinance as yf
import pandas as pd
from telegram import Bot
from datetime import datetime

def run():
    try:
        # Vérification des variables d’environnement
        GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
        TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
        CHAT_ID = os.environ.get("CHAT_ID")

        if not all([GOOGLE_SHEET_ID, TELEGRAM_TOKEN, CHAT_ID]):
            raise ValueError("Une ou plusieurs variables d’environnement sont manquantes.")

        # Connexion à Google Sheets
        creds_path = "/etc/secrets/credentials.json"
        if not os.path.exists(creds_path):
            raise FileNotFoundError("Fichier credentials.json introuvable.")

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        tickers = sheet.col_values(1)[1:]  # ignore l'en-tête

        if not tickers:
            raise ValueError("La liste de tickers dans Google Sheets est vide.")

        # Initialisation de Telegram
        bot = Bot(token=TELEGRAM_TOKEN)
        messages = []

        for ticker in tickers:
            data = yf.download(ticker, period="1mo", interval="1d")
            if data.empty or len(data) < 30:
                continue

            # VOLATILITÉ
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

        final_message = "\n".join(messages) if messages else "Aucun signal détecté aujourd'hui."
        bot.send_message(chat_id=CHAT_ID, text=final_message)

        return "Analyse envoyée avec succès ✅"
    except Exception as e:
        print(f"[ERREUR] {e}")  # Affiche dans les logs Render
        return f"Erreur : {e}"
