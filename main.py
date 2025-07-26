import os
import json
import gspread
import yfinance as yf
from google.oauth2.service_account import Credentials
import telegram
from flask import Flask

app = Flask(__name__)

@app.route("/")
def analyse_boursiere():
    try:
        # 🔐 Authentification Google Sheets via secret file
        with open("/etc/secrets/credentials.json") as f:
            creds_dict = json.load(f)

        creds = Credentials.from_service_account_info(creds_dict)
        gc = gspread.authorize(creds)

        # 📄 Lecture des tickers depuis Google Sheets
        sheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"]).sheet1
        tickers = sheet.col_values(1)[1:]  # Ignorer l'en-tête

        messages = []

        for ticker in tickers:
            try:
                data = yf.download(ticker, period="7d", interval="1d")

                if data.empty:
                    messages.append(f"⚠️ Aucune donnée pour {ticker}")
                    continue

                # Analyse Ichimoku
                data["tenkan_sen"] = (data["High"].rolling(window=9).max() + data["Low"].rolling(window=9).min()) / 2
                data["kijun_sen"] = (data["High"].rolling(window=26).max() + data["Low"].rolling(window=26).min()) / 2

                dernier = data.iloc[-1]
                if dernier["tenkan_sen"] > dernier["kijun_sen"]:
                    messages.append(f"📈 Signal haussier Ichimoku sur {ticker}")
                elif dernier["tenkan_sen"] < dernier["kijun_sen"]:
                    messages.append(f"📉 Signal baissier Ichimoku sur {ticker}")
                else:
                    messages.append(f"➖ Aucune tendance nette sur {ticker}")

            except Exception as e:
                messages.append(f"❌ Erreur sur {ticker} : {e}")

        # Envoi via Telegram
        bot = telegram.Bot(token=os.environ["TELEGRAM_TOKEN"])
        final_msg = "\n".join(messages) or "✅ Aucune alerte détectée"
        bot.send_message(chat_id=os.environ["CHAT_ID"], text=final_msg)

        return "✅ Analyse terminée", 200

    except Exception as e:
        return f"❌ Erreur : {e}", 500
