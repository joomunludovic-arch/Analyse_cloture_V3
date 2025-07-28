import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot
import os
from datetime import datetime, timedelta

# 🔐 Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 📊 Liste d'exemples (personnalisable)
tickers = [
    "TSLA", "AAPL", "NVDA", "AMZN", "META", "MSFT", "NFLX",
    "^GSPC", "^IXIC", "^DJI", "BTC-USD", "ETH-USD", "XAUUSD=X"
]

# 📈 Calcul des indicateurs Ichimoku
def ichimoku_cloud(df):
    df['tenkan_sen'] = (df['High'].rolling(9).max() + df['Low'].rolling(9).min()) / 2
    df['kijun_sen'] = (df['High'].rolling(26).max() + df['Low'].rolling(26).min()) / 2
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    df['senkou_span_b'] = ((df['High'].rolling(52).max() + df['Low'].rolling(52).min()) / 2).shift(26)
    df['chikou_span'] = df['Close'].shift(-26)
    return df

# ✅ Détection opportunité cash-flow
def detect_cashflow_opportunity(df):
    last = df.iloc[-1]
    return (
        last['Close'] > last['kijun_sen']
        and last['Close'] > last['senkou_span_a']
        and last['Close'] > last['senkou_span_b']
        and last['tenkan_sen'] > last['kijun_sen']
    )

# ✉️ Envoi Telegram
def send_telegram_photo(image, caption):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_photo(chat_id=CHAT_ID, photo=image, caption=caption, parse_mode="Markdown")

# 🚀 Fonction principale
def run():
    fin = datetime.now()
    debut = fin - timedelta(days=90)
    messages = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, start=debut, end=fin, interval="1d")
            if df.empty or len(df) < 60:
                continue

            df = ichimoku_cloud(df)
            df['volatility'] = df['Close'].pct_change().rolling(10).std()

            if detect_cashflow_opportunity(df):
                latest = df.iloc[-1]

                # Graphique Ichimoku
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(df.index, df['Close'], label="Clôture", linewidth=2)
                ax.plot(df.index, df['tenkan_sen'], label="Tenkan Sen", linestyle='--')
                ax.plot(df.index, df['kijun_sen'], label="Kijun Sen", linestyle='--')
                ax.plot(df.index, df['senkou_span_a'], label="Senkou Span A", linestyle=':')
                ax.plot(df.index, df['senkou_span_b'], label="Senkou Span B", linestyle=':')

                ax.fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'],
                                where=df['senkou_span_a'] >= df['senkou_span_b'],
                                color='lightgreen', alpha=0.3)
                ax.fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'],
                                where=df['senkou_span_a'] < df['senkou_span_b'],
                                color='lightcoral', alpha=0.3)

                ax.set_title(f"{ticker} - Opportunité Cash-Flow ({fin.date()})")
                ax.legend()

                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plt.close()

                caption = (
                    f"*{ticker}* : opportunité détectée 📈\n"
                    f"Clôture : `{latest['Close']:.2f}` | Volatilité 10j : `{latest['volatility']:.2%}`\n"
                    f"_Signaux Ichimoku favorables à l’achat._"
                )

                send_telegram_photo(buf, caption=caption)
                messages.append(f"{ticker} ✅")
        except Exception as e:
            messages.append(f"{ticker} ❌ Erreur : {e}")

    return "📊 Résumé :\n" + "\n".join(messages) if messages else "Aucune opportunité détectée."
