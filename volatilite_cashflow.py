import yfinance as yf
import telegram
import os
from datetime import datetime, timedelta

def analyse_volatilite_cashflow():
    tickers = [
        "TSLA", "AAPL", "NVDA", "MSFT", "META", "AMZN", "AMD", "GOOGL", "NFLX", "BABA",
        "^FCHI", "^GSPC", "^IXIC", "BTC-USD", "ETH-USD"
    ]

    resultats = []
    erreurs = []

    for ticker in tickers:
        try:
            data = yf.download(ticker, period="5d", interval="1d", progress=False)
            if len(data) < 5:
                erreurs.append(ticker)
                continue

            data['variation'] = data['Close'].pct_change()
            volatilite = data['variation'].std()
            derniere_cloture = data['Close'].iloc[-1]
            cashflow_potentiel = round(volatilite * derniere_cloture * 100, 2)

            resultats.append({
                "ticker": ticker,
                "volatilite": round(volatilite * 100, 2),
                "cours": round(derniere_cloture, 2),
                "cashflow": cashflow_potentiel
            })
        except Exception as e:
            erreurs.append(f"{ticker}: {str(e)}")

    resultats.sort(key=lambda x: x['volatilite'], reverse=True)
    top_resultats = resultats[:5]

    message = "📊 Analyse Clôture - Top Cash-Flow Potentiel :\n\n"
    for res in top_resultats:
        message += f"🔹 {res['ticker']} | {res['cours']} € | 📈 Vol : {res['volatilite']}% | 💶 Pot. : {res['cashflow']} €\n"
    message += "\n💬 Bourses fermées : données clôture utilisées."

    # Envoi Telegram
    bot = telegram.Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    bot.send_message(chat_id=chat_id, text=message)

    return message
