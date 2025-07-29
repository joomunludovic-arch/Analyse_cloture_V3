import os
import gspread
import yfinance as yf
import pandas as pd
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot, constants

def run():
    try:
        # ✅ Initialisation du bot Telegram
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        bot = Bot(token=token)

        # 🔐 Authentification Google Sheets
        creds_path = "/etc/secrets/credentials.json"
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)

        # 📄 Lecture des tickers
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet(0)
        tickers = worksheet.col_values(1)[1:]  # Ignorer l'en-tête

        messages = []

        for ticker in tickers:
            data = yf.download(ticker, period="30d", interval="1d", progress=False)
            if data.empty or len(data) < 26:
                messages.append(f"⚠️ {ticker} : Données insuffisantes.")
                continue

            # 🔍 Volatilité
            data["Returns"] = data["Close"].pct_change()
            volatility = data["Returns"].std() * np.sqrt(252)

            # 📈 Ichimoku
            high_9 = data["High"].rolling(window=9).max()
            low_9 = data["Low"].rolling(window=9).min()
            tenkan_sen = (high_9 + low_9) / 2

            high_26 = data["High"].rolling(window=26).max()
            low_26 = data["Low"].rolling(window=26).min()
            kijun_sen = (high_26 + low_26) / 2

            # 🟢 Signal haussier
            if tenkan_sen.iloc[-2] < kijun_sen.iloc[-2] and tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]:
                messages.append(
                    f"🔔 *{ticker}* : Signal *Ichimoku haussier* détecté\nVolatilité : *{volatility:.2%}*"
                )

        # 📬 Envoi Telegram
        if messages:
            bot.send_message(
                chat_id=chat_id,
                text="\n\n".join(messages),
                parse_mode=constants.ParseMode.MARKDOWN
            )
            return f"{len(messages)} signal(s) détecté(s) et envoyé(s) ✅"
        else:
            # ✅ Envoi d’un message même sans signal
            bot.send_message(chat_id=chat_id, text="🟡 Aucun signal détecté aujourd'hui.")
            return "Aucun signal détecté aujourd'hui."

    except Exception as e:
        try:
            bot.send_message(chat_id=chat_id, text=f"❌ Erreur détectée : {str(e)}")
        except:
            pass
        return f"Erreur détectée : {str(e)}"
