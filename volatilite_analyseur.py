import yfinance as yf
from telegram import Bot
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Liste des tickers à surveiller — tu peux l’étendre
TICKERS = [
    "TSLA", "NVDA", "AMD", "AAPL", "META", "AMZN", "NFLX",
    "^GSPC", "^IXIC", "^DJI", "BTC-USD", "ETH-USD", "DOGE-USD"
]

def calcul_volatilite(ticker):
    try:
        data = yf.download(ticker, period="10d", interval="1d")
        if data.empty or "Close" not in data:
            return None
        returns = data["Close"].pct_change().dropna()
        volatilite = returns.std()
        return round(volatilite, 4)
    except Exception as e:
        print(f"Erreur pour {ticker} : {e}")
        return None

def analyser_volatilite():
    resultats = []
    for ticker in TICKERS:
        vol = calcul_volatilite(ticker)
        if vol is not None:
            resultats.append((ticker, vol))

    if not resultats:
        return "Aucune donnée de volatilité récupérée."

    # Tri par volatilité décroissante
    resultats.sort(key=lambda x: x[1], reverse=True)
    top5 = resultats[:5]

    message = "📊 *TOP 5 Volatilité (10 jours)* :\n\n"
    for t, v in top5:
        message += f"• {t} : {v * 100:.2f}%\n"

    # Envoi sur Telegram
    if TELEGRAM_TOKEN and CHAT_ID:
        try:
            bot = Bot(token=TELEGRAM_TOKEN)
            bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        except Exception as e:
            message += f"\n⚠️ Erreur Telegram : {e}"

    return message
