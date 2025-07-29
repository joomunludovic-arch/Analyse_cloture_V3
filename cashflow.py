import os
import yfinance as yf
import matplotlib.pyplot as plt
from telegram import Bot
from telegram.constants import ParseMode

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

tickers = ["TSLA", "NVDA", "AMD", "AAPL", "BE", "GOLD", "BTC-USD", "ETH-USD"]

async def run_cashflow():
    try:
        data = {}
        for t in tickers:
            df = yf.download(t, period="7d", interval="1d")
            if len(df) >= 2:
                volatility = df["Close"].pct_change().std() * 100
                data[t] = {
                    "volatilite": round(volatility, 2),
                    "cloture": round(df["Close"].iloc[-1], 2),
                }

        top = sorted(data.items(), key=lambda x: x[1]["volatilite"], reverse=True)[:5]
        msg = "📊 *Top 5 volatilité (7j)*\n\n"
        for t, val in top:
            msg += f"*{t}* : {val['volatilite']} % | Clôture: {val['cloture']}\n"

        # Barplot
        labels = [t for t, _ in top]
        values = [v["volatilite"] for _, v in top]
        plt.figure()
        plt.bar(labels, values)
        plt.title("Top 5 Volatilité (7j)")
        plt.xlabel("Ticker")
        plt.ylabel("Volatilité (%)")
        plt.tight_layout()
        plt.savefig("volatilite.png")

        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_photo(chat_id=CHAT_ID, photo=open("volatilite.png", "rb"))
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.MARKDOWN)

        return "✅ Cashflow envoyé"

    except Exception as e:
        return f"❌ Erreur cashflow : {e}"
