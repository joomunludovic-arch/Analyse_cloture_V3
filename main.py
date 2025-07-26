from flask import Flask
import os
import json
import gspread
import yfinance as yf
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
import requests

app = Flask(__name__)

# 🔐 Auth Google Sheets depuis variable d’environnement
def load_google_sheet_client():
    creds_json = os.getenv("GOOGLE_CREDS_JSON")
    if not creds_json:
        raise ValueError("❌ GOOGLE_CREDS_JSON non définie.")
    
    creds_dict = json.loads(creds_json)
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(credentials)
    return client

# 📊 Récupération des tickers depuis Google Sheets
def get_tickers(sheet_id):
    client = load_google_sheet_client()
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.sheet1
    tickers = worksheet.col_values(1)
    return [t.strip().upper() for t in tickers if t.strip()]

# 📈 Analyse Ichimoku + Volatilité
def analyse_titre(ticker):
    try:
        df = yf.download(ticker, period="2mo", interval="1d")
        if df.empty or len(df) < 52:
            return f"{ticker} : Données insuffisantes"

        # Ichimoku
        nine_period_high = df['High'].rolling(window=9).max()
        nine_period_low = df['Low'].rolling(window=9).min()
        df['tenkan_sen'] = (nine_period_high + nine_period_low) / 2
        period26_high = df['High'].rolling(window=26).max()
        period26_low = df['Low'].rolling(window=26).min()
        df['kijun_sen'] = (period26_high + period26_low) / 2
        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
        period52_high = df['High'].rolling(window=52).max()
        period52_low = df['Low'].rolling(window=52).min()
        df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)

        tenkan = df['tenkan_sen'].iloc[-1]
        kijun = df['kijun_sen'].iloc[-1]
        close = df['Close'].iloc[-1]

        tendance = ""
        if tenkan > kijun and close > tenkan:
            tendance = "📈 Tendance haussière"
        elif tenkan < kijun and close < tenkan:
            tendance = "📉 Tendance baissière"
        else:
            tendance = "⚖️ Tendance neutre"

        # Volatilité
        df['returns'] = df['Close'].pct_change()
        volatility = np.std(df['returns'].tail(20)) * 100
        vol_comment = "🟢 Faible volatilité" if volatility < 2 else "🟠 Volatilité modérée" if volatility < 5 else "🔴 Forte volatilité"

        return f"{ticker} → {tendance} | {vol_comment} ({volatility:.2f}%)"
    
    except Exception as e:
        return f"{ticker} : Erreur d'analyse ({str(e)})"

# 📬 Envoi Telegram
def envoyer_telegram(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    if not token or not chat_id:
        raise ValueError("❌ Token Telegram ou Chat ID manquant.")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    if not response.ok:
        raise Exception(f"Erreur Telegram : {response.text}")

# 🚀 Route d’analyse déclenchée par Google Apps Script
@app.route("/", methods=["GET"])
def analyser():
    try:
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        tickers = get_tickers(sheet_id)
        messages = [analyse_titre(t) for t in tickers]
        final_msg = "\n".join(messages)
        envoyer_telegram(final_msg)
        return "✅ Analyse envoyée avec succès", 200
    except Exception as e:
        return f"❌ Erreur : {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
