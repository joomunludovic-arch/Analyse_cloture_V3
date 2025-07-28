import yfinance as yf
import matplotlib.pyplot as plt
import io
import os
import telegram
import pandas as pd
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def detecter_volatilite():
    tickers = [
        "TSLA", "AAPL", "NVDA", "AMZN", "META", "MSFT", "NFLX",
        "^GSPC", "^IXIC", "^DJI", "BTC-USD", "ETH-USD", "XAUUSD=X"
    ]

    fin = datetime.now()
    debut = fin - timedelta(days=7)
    meilleurs = []

    for ticker in tickers:
        data = yf.download(ticker, start=debut, end=fin)
        if data.empty:
            continue
        volatilite = data['Close'].pct_change().std()
        derniers = data['Close'][-1]
        meilleurs.append((ticker, volatilite, derniers))

    meilleurs.sort(key=lambda x: x[1], reverse=True)
    top = meilleurs[:5]

    fig, ax = plt.subplots()
    noms = [x[0] for x in top]
    vols = [x[1] for x in top]
    ax.bar(noms, vols)
    ax.set_title("Top 5 volatilités")
    ax.set_ylabel("Volatilité (écart-type)")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    message = "*Top 5 actions à forte volatilité :*\n\n"
    for sym, vol, close in top:
        message += f"• {sym} : volatilité = {vol:.4f} | cours = {close:.2f}\n"
    message += "\n_Stratégie_: surveiller ces titres à l’ouverture."

    bot.send_photo(chat_id=CHAT_ID, photo=buf)
    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    return "Analyse de volatilité transmise avec succès."
