from flask import Flask
import telegram
import yfinance as yf
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

app = Flask(__name__)

# 🔐 Initialisation des variables d'environnement
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_CREDS_JSON")

# 🔧 Configuration Telegram
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# 📊 Connexion Google Sheets
def get_tickers_from_sheet():
    import json
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    tickers = sheet.col_values(1)[1:]  # Ignore l'en-tête
    return tickers

# 📈 Analyse Ichimoku et Volatilité
def analyse_action(ticker):
    try:
        df = yf.download(ticker, period='3mo', interval='1d')
        if df.empty or len(df) < 52:
            return f"Pas assez de données pour {ticker}"

        # Calcul Ichimoku
        df['tenkan_sen'] = (df['High'].rolling(window=9).max() + df['Low'].rolling(window=9).min()) / 2
        df['kijun_sen'] = (df['High'].rolling(window=26).max() + df['Low'].rolling(window=26).min()) / 2

        # Analyse Ichimoku
        tenkan = df['tenkan_sen'].iloc[-1]
        kijun = df['kijun_sen'].iloc[-1]
        price = df['Close'].iloc[-1]
        ichimoku_signal = ""
        if tenkan > kijun and price > tenkan:
            ichimoku_signal = "Signal Ichimoku : 🟢 Achat"
        elif tenkan < kijun and price < tenkan:
            ichimoku_signal = "Signal Ichimoku : 🔴 Vente"
        else:
            ichimoku_signal = "Signal Ichimoku : ⚪ Neutre"

        # Analyse Volatilité
        df['returns'] = df['Close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=14).std()
        vol = df['volatility'].iloc[-1]
        vol_signal = ""
        if vol > 0.03:
            vol_signal = f"Volatilité élevée ({vol:.2%})"
        elif vol < 0.01:
            vol_signal = f"Volatilité faible ({vol:.2%})"
        else:
            vol_signal = f"Volatilité modérée ({vol:.2%})"

        return f"{ticker} : {ichimoku_signal} | {vol_signal}"

    except Exception as e:
        return f"Erreur sur {ticker} : {str(e)}"

# 🔁 Lancement de l'analyse
@app.route('/')
def run_analysis():
    try:
        tickers = get_tickers_from_sheet()
        messages = []
        for ticker in tickers:
            result = analyse_action(ticker)
            messages.append(result)

        final_message = "\n".join(messages)
        bot.send_message(chat_id=CHAT_ID, text=f"📊 Résultats analyse du jour :\n\n{final_message}")
        return "✅ Analyse envoyée sur Telegram"
    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"❌ Erreur analyse : {str(e)}")
        return f"Erreur : {str(e)}"

# ▶️ Point d'entrée Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
