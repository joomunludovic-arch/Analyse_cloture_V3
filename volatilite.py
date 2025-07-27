import yfinance as yf
from telegram import Bot
import os

def run_volatilite():
    tickers = ["TSLA", "NVDA", "AAPL", "META", "AMZN", "NFLX", "AMD", "GOOGL"]
    seuil_volatilite = 0.03
    resultats = []

    for ticker in tickers:
        data = yf.download(ticker, period="7d", interval="1d")
        if len(data) < 2:
            continue

        data["variation"] = abs(data["Close"].pct_change())
        volatilite_moyenne = data["variation"].mean()

        if volatilite_moyenne > seuil_volatilite:
            resultats.append(f"{ticker} 📈 volatilité moyenne : {volatilite_moyenne:.2%}")

    if resultats:
        message = "🔥 Actions à forte volatilité détectées :\n\n" + "\n".join(resultats)
    else:
        message = "Aucune action volatile détectée."

    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("CHAT_ID")
    if token and chat_id:
        bot = Bot(token=token)
        bot.send_message(chat_id=chat_id, text=message)

    return message
