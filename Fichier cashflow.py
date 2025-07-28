import os
import gspread
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot
from io import BytesIO
import datetime

# Config
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDS_JSON = "/etc/secrets/credentials.json"

def ichimoku_signals(df):
    nine_high = df['High'].rolling(window=9).max()
    nine_low = df['Low'].rolling(window=9).min()
    df['tenkan_sen'] = (nine_high + nine_low) / 2

    period26_high = df['High'].rolling(window=26).max()
    period26_low = df['Low'].rolling(window=26).min()
    df['kijun_sen'] = (period26_high + period26_low) / 2

    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    df['senkou_span_b'] = ((df['High'].rolling(window=52).max() + df['Low'].rolling(window=52).min()) / 2).shift(26)
    df['chikou_span'] = df['Close'].shift(-26)

    latest = df.iloc[-1]
    if (
        latest['Close'] > latest['senkou_span_a'] and
        latest['Close'] > latest['senkou_span_b'] and
        latest['tenkan_sen'] > latest['kijun_sen']
    ):
        return True
    return False

def calculate_volatility(df):
    df['returns'] = df['Close'].pct_change()
    return df['returns'].std() * np.sqrt(252)

def send_telegram_image(bot, image_bytes, caption):
    bot.send_photo(chat_id=CHAT_ID, photo=image_bytes, caption=caption)

def run():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_JSON, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        tickers = sheet.sheet1.col_values(1)

        bot = Bot(token=TOKEN)
        messages = []
        today = datetime.date.today()

        for ticker in tickers:
            try:
                data = yf.download(ticker, period="6mo", interval="1d")
                if data.empty or len(data) < 60:
                    continue

                vol = calculate_volatility(data)
                ichimoku_ok = ichimoku_signals(data)

                if vol > 0.4 and ichimoku_ok:
                    last_close = data['Close'].iloc[-1]

                    # Graphique
                    fig, ax = plt.subplots()
                    data['Close'].tail(60).plot(ax=ax, label='Clôture')
                    data['tenkan_sen'].tail(60).plot(ax=ax, label='Tenkan')
                    data['kijun_sen'].tail(60).plot(ax=ax, label='Kijun')
                    ax.set_title(f"{ticker} - Clôture et Ichimoku")
                    ax.legend()

                    buf = BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    plt.close()

                    caption = f"📊 {ticker}\n💥 Volatilité : {vol:.2f}\n📈 Clôture : {last_close:.2f}\n📌 Signal d'achat détecté."
                    send_telegram_image(bot, buf, caption)
                    messages.append(caption)
            except Exception as e:
                messages.append(f"⚠️ {ticker} erreur : {e}")

        if not messages:
            bot.send_message(chat_id=CHAT_ID, text="Aucune opportunité détectée aujourd’hui.")
        return "Analyse cash-flow envoyée sur Telegram ✅"
    except Exception as e:
        return f"Erreur dans cashflow.py : {e}"
