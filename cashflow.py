import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot
import os
import numpy as np
from datetime import datetime, timedelta

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Liste d'exemples (à remplacer ou étendre avec une source dynamique)
tickers = ["TSLA", "NVDA", "AAPL", "META", "AMD", "NFLX", "AMZN", "COIN", "BIDU", "MSFT"]

def ichimoku_cloud(df):
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

    df['chikou_span'] = df['Close'].shift(-26)

    return df

def detect_cashflow_opportunity(df):
    latest = df.iloc[-1]
    return (
        latest['Close'] > latest['kijun_sen']
        and latest['Close'] > latest['senkou_span_a']
        and latest['Close'] > latest['senkou_span_b']
        and latest['tenkan_sen'] > latest['kijun_sen']
    )

def send_telegram_photo(image_bytes, caption="Analyse cash-flow"):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_photo(chat_id=CHAT_ID, photo=image_bytes, caption=caption)

def run():
    messages = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="3mo", interval="1d")
            if len(df) < 60:
                continue

            df = ichimoku_cloud(df)
            df['volatility'] = df['Close'].pct_change().rolling(window=10).std()

            if detect_cashflow_opportunity(df):
                latest = df.iloc[-1]
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(df.index, df['Close'], label="Clôture")
                ax.plot(df.index, df['tenkan_sen'], label="Tenkan Sen")
                ax.plot(df.index, df['kijun_sen'], label="Kijun Sen")
                ax.plot(df.index, df['senkou_span_a'], label="Senkou Span A")
                ax.plot(df.index, df['senkou_span_b'], label="Senkou Span B")
                ax.fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'],
                                where=(df['senkou_span_a'] >= df['senkou_span_b']),
                                color='lightgreen', alpha=0.4)
                ax.fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'],
                                where=(df['senkou_span_a'] < df['senkou_span_b']),
                                color='lightcoral', alpha=0.4)
                ax.set_title(f"{ticker} - Cash-Flow Opportunity")
                ax.legend()

                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png')
                buf.seek(0)

                caption = (
                    f"{ticker} : Signal à fort potentiel de cash-flow 📈\n"
                    f"Clôture : {latest['Close']:.2f} | Volatilité 10j : {latest['volatility']:.2%}"
                )

                send_telegram_photo(buf, caption=caption)
                messages.append(caption)
                plt.close()
        except Exception as e:
            messages.append(f"{ticker} : erreur d’analyse ({e})")

    return "\n".join(messages) if messages else "Aucune opportunité détectée."
