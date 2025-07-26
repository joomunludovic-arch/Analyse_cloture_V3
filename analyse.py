import pandas as pd
import yfinance as yf
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from datetime import datetime

# 📌 Configuration
TELEGRAM_TOKEN = '8415756245:AAHaU2KBRsC3q05eLld2JjMt_V7S9j-o4ys'
TELEGRAM_CHAT_ID = '5814604646'

# Autorisation Google Sheets
def lire_tickers():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1-hPKh5yJq6F-eboLbsG8sLxwdesI9LPH2L08emI7i6g").sheet1
    return sheet.col_values(1)[1:]  # Ignore l'en-tête

# Analyse Ichimoku simplifiée
def ichimoku_signal(df):
    nine_period_high = df['High'].rolling(window=9).max()
    nine_period_low = df['Low'].rolling(window=9).min()
    df['tenkan_sen'] = (nine_period_high + nine_period_low) / 2
    df['kijun_sen'] = df['Close'].rolling(window=26).mean()
    return df['tenkan_sen'].iloc[-1] > df['kijun_sen'].iloc[-1]

# Analyse de volatilité simplifiée
def volatilite_signal(df):
    df['retour'] = df['Close'].pct_change()
    volatilite = df['retour'].rolling(window=5).std().iloc[-1]
    return volatilite > 0.03  # seuil ajustable

# Envoi Telegram
def envoyer_alerte(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    requests.post(url, data=data)

def lancer_analyse():
    tickers = lire_tickers()
    messages = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period='1mo', interval='1d')
            if df.empty:
                continue
            signal_ichimoku = ichimoku_signal(df)
            signal_volatilite = volatilite_signal(df)

            if signal_ichimoku or signal_volatilite:
                message = f"📈 Signal détecté sur {ticker} ({'Ichimoku' if signal_ichimoku else ''} {'Volatilité' if signal_volatilite else ''})"
                envoyer_alerte(message)
                messages.append(message)
        except Exception as e:
            messages.append(f"❌ Erreur {ticker}: {str(e)}")

    return "\n".join(messages) if messages else "Aucun signal détecté"
