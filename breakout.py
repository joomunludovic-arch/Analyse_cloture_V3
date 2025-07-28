import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

tickers = ["TSLA", "AAPL", "NVDA", "META", "AMZN", "MSFT", "NFLX", "AMD", "COIN", "BIDU"]

def calculate_ichimoku(df):
    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    df['tenkan_sen'] = (high_9 + low_9) / 2

    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['kijun_sen'] = (high_26 + low_26) / 2

    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['senkou_span_b'] = ((high_52 + low_52) / 2).shift(26)

    df['chikou_span'] = df['Close'].shift(-26)
    return df

def detect_breakout(df):
    latest = df.iloc[-1]
    return (
        latest['Close'] > latest['tenkan_sen']
        and latest['Close'] > latest['kijun_sen']
        and latest['tenkan_sen'] > latest['kijun_sen']
        and latest['Close'] > latest['senkou_span_a']
        and latest['Close'] > latest['senkou_span_b']
    )

def run():
    bot = Bot(token=TELEGRAM_TOKEN)
    messages = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="3mo", interval="1d")
            if df.empty or len(df) < 60:
                continue

            df = calculate_ichimoku(df)

            if detect_breakout(df):
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(df.index, df['Close'], label="Clôture", linewidth=2)
                ax.plot(df.index, df['tenkan_sen'], label="Tenkan", linestyle="--")
                ax.plot(df.index, df['kijun_sen'], label="Kijun", linestyle="--")
                ax.plot(df.index, df['senkou_span_a'], label="Senkou A", linestyle=":")
                ax.plot(df.index, df['senkou_span_b'], label="Senkou B", linestyle=":")
                ax.fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'],
                                where=df['senkou_span_a'] >= df['senkou_span_b'],
                                color='lightgreen', alpha=0.3)
                ax.fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'],
                                where=df['senkou_span_a'] < df['senkou_span_b'],
                                color='lightcoral', alpha=0.3)
                ax.set_title(f"{ticker} - Breakout Ichimoku")
                ax.legend()

                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plt.close()

                bot.send_photo(chat_id=CHAT_ID, photo=buf, caption=f"{ticker} : Breakout détecté 🚀")
                messages.append(f"{ticker} ✅")
        except Exception as e:
            messages.append(f"{ticker} ❌ Erreur : {e}")

    return "Résultat breakout :\n" + "\n".join(messages) if messages else "Aucun breakout détecté."
