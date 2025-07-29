import os
import json
import gspread
import yfinance as yf
import pandas as pd
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot

def run():
    try:
        # 🔐 Lecture des credentials Google Sheets depuis le fichier monté
        creds_path = "/etc/secrets/credentials.json"
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)

        # 📄 Récupération des tickers depuis la feuille Google Sheets
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet(0)
        tickers = worksheet.col_values(1)[1:]  # Ignore l'en-tête

        # 🔄 Boucle d’analyse
        messages = []
        for ticker in tickers:
            data = yf.download(ticker, period="30d", interval="1d", progress=False)
            if data.empty or len(data) < 26:
                messages.append(f"{ticker}: Données insuffisantes")
                continue

            # 📉 Calcul de la volatilité (écart-type des variations journalières)
            data["Returns"] = data["Close"].pct_change()
            volatility = data["Returns"].std() * np.sqrt(252)

            # 📈 Calcul de l'Ichimoku
            high_9 = data["High"].rolling(window=9).max()
            low_9 = data["Low"].rolling(window=9).min()
            tenkan_sen = (high_9 + low_9) / 2

            high_26 = data["High"].rolling(window=26).max()
            low_26 = data["Low"].rolling(window=26).min()
            kijun_sen = (high_26 + low_26) / 2

            # 🟢 Signal Ichimoku : Tenkan croise au-dessus de Kijun
            if tenkan_sen.iloc[-2] < kijun_sen.iloc[-2] and tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]:
                messages.append(f"🔔 Signal Ichimoku haussier détecté sur {ticker} (Volatilité: {volatility:.2%})")

        # 📬 Envoi Telegram
        if messages:
            token = os.getenv("TELEGRAM_TOKEN")
            chat_id = os.getenv("CHAT_ID")
            bot = Bot(token=token)
            bot.send_message(chat_id=chat_id, text="\n".join(messages))
            return f"{len(messages)} signal(s) envoyé(s)."
        else:
            return "Aucun signal détecté aujourd'hui."

    except Exception as e:
        return f"Erreur dans l'analyseur : {str(e)}"

try:
    tickers = get_tickers_from_google_sheet()
    resultats = analyse_tous_les_titres(tickers)

    
if resultats:
        for message in resultats:
            bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=constants.ParseMode.MARKDOWN)
        return {"message": f"{len(resultats)} signaux détectés et envoyés 📈"}
    else:
        bot.send_message(chat_id=CHAT_ID, text="🟡 Aucun signal détecté aujourd'hui.")
        return {"message": "Aucun signal détecté aujourd'hui."}

except Exception as e:
    bot.send_message(chat_id=CHAT_ID, text=f"❌ Erreur détectée : {str(e)}")
    return {"message": f"Erreur détectée : {str(e)}"}
