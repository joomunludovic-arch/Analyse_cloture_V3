import yfinance as yf
import telegram
import os
import matplotlib.pyplot as plt
from io import BytesIO
import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def run():
    tickers = ["TSLA", "NVDA", "AAPL", "META", "AMD", "NFLX", "COIN", "SHOP", "GME", "RIVN"]
    results = []

    for ticker in tickers:
        data = yf.download(ticker, period="15d", interval="1d")
        if len(data) < 2:
            continue

        data["Volatility"] = data["High"] - data["Low"]
        recent = data.iloc[-1]
        avg_volatility = data["Volatility"].mean()
        is_high = recent["Volatility"] > avg_volatility * 1.2

        if is_high:
            results.append((ticker, recent["Volatility"], avg_volatility))

            plt.figure(figsize=(10, 4))
            data["Volatility"].plot(title=f"{ticker} - Volatilité")
            buf = BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)

            bot = telegram.Bot(token=TELEGRAM_TOKEN)
            bot.send_photo(chat_id=CHAT_ID, photo=buf,
                           caption=f"🔥 {ticker} présente une forte volatilité aujourd'hui !\nVolatilité : {recent['Volatility']:.2f} vs Moyenne : {avg_volatility:.2f}")

    if not results:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=CHAT_ID, text="📉 Aucune volatilité exceptionnelle détectée aujourd’hui.")

    return f"{len(results)} tickers détectés à forte volatilité"
