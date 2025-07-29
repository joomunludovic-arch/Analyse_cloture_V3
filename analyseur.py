import os
import yfinance as yf
import pandas as pd
import numpy as np
import gspread
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot
from telegram.constants import ParseMode


def get_tickers_from_google_sheet():
    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    GOOGLE_CREDS_JSON = "/etc/secrets/credentials.json"

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_JSON, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    tickers = sheet.col_values(1)[1:]  # Ignore l’en-tête
    return [ticker.strip().upper() for ticker in tickers if ticker.strip()]


def calculate_ichimoku(df):
    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    df['tenkan_sen'] = (high_9 + low_9) / 2

    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['kijun_sen'] = (high_26 + low_26) / 2

    df['chikou_span'] = df['Close'].shift(-26)
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)

    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['senkou_span_b'] = ((high_52 + low_52) / 2).shift(26)

    return df


def is_bullish_signal(df):
    latest = df.iloc[-1]
    return latest['tenkan_sen'] > latest['kijun_sen'] and latest['Close'] > latest['kijun_sen']


async def send_telegram_message(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    bot = Bot(token=token)
    await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)


async def test_telegram_send():
    try:
        await send_telegram_message("✅ Test réussi ! Ton bot Telegram fonctionne bien 🔥")
        return "✅ Message Telegram envoyé avec succès."
    except Exception as e:
        return f"❌ Erreur lors de l’envoi Telegram : {e}"


async def run():
    try:
        tickers = get_tickers_from_google_sheet()
        bullish_signals = []

        for ticker in tickers:
            df = yf.download(ticker, period="3mo", interval="1d")
            if df.empty or len(df) < 60:
                continue
            df = calculate_ichimoku(df)
            if is_bullish_signal(df):
                latest_close = df['Close'].iloc[-1]
                bullish_signals.append(f"📈 *{ticker}* → Clôture: {latest_close:.2f} € ✅")

        if bullish_signals:
            message = "*Signaux Ichimoku détectés à la clôture :*\n\n" + "\n".join(bullish_signals)
        else:
            message = "📉 Aucun signal Ichimoku détecté aujourd’hui."

        await send_telegram_message(message)
        return "✅ Analyse terminée et message Telegram envoyé."
    except Exception as e:
        return f"❌ Erreur pendant l’analyse : {e}"


# Code déclenchable pour test direct
if __name__ == "__main__":
    print("Analyseur exécuté manuellement.")
    print("Lance l’analyse complète...")
    result = asyncio.run(run())
    print(result)
