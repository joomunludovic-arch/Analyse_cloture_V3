import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import telegram
from io import BytesIO
import os
from datetime import datetime, timedelta

# Configuration
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telegram.Bot(token=TOKEN)

# Liste d’actions à analyser (modifiable)
TICKERS = [
    "TSLA", "AAPL", "NVDA", "AMD", "META", "NFLX", "GOOG", "AMZN", "MSFT", "BIDU",
    "COIN", "SHOP", "BABA", "UBER", "NIO", "SOFI", "SNAP", "TWLO", "PLTR", "INTC"
]

def detect_cashflow_opportunities(ticker):
    try:
        df = yf.download(ticker, period="7d", interval="1d")
        if df.empty or len(df) < 2:
            return None, None

        df['Volatility'] = df['High'] - df['Low']
        df['Daily %'] = ((df['Close'] - df['Open']) / df['Open']) * 100

        last_volatility = df['Volatility'].iloc[-1]
        last_percent = df['Daily %'].iloc[-1]

        if last_volatility > df['Volatility'].mean() * 1.5 and abs(last_percent) > 2:
            fig, ax = plt.subplots()
            df[['Open', 'Close']].plot(ax=ax, title=f"{ticker} - Dernières clôtures")
            ax.set_ylabel("Prix")
            plt.grid(True)

            buf = BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            plt.close()

            return f"💹 {ticker} : 🔥 Volatilité détectée ({last_percent:.2f}%)", buf
        return None, None
    except Exception as e:
        return f"⚠️ Erreur pour {ticker} : {e}", None

def run():
    messages = []
    count = 0

    for ticker in TICKERS:
        msg, chart = detect_cashflow_opportunities(ticker)
        if msg:
            count += 1
            if chart:
                bot.send_photo(chat_id=CHAT_ID, photo=chart, caption=msg)
            else:
                bot.send_message(chat_id=CHAT_ID, text=msg)
            messages.append(msg)

    if not messages:
        bot.send_message(chat_id=CHAT_ID, text="📉 Aucune opportunité de cash-flow détectée aujourd'hui.")
    return f"{count} opportunités détectées." if count else "Aucune action pertinente."
