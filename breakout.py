import os
import yfinance as yf
from telegram import Bot
from telegram.constants import ParseMode

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

tickers = ["BE", "TSLA", "AAPL", "NVDA"]

async def run_breakout():
    try:
        signals = []
        for ticker in tickers:
            df = yf.download(ticker, period="1mo", interval="1d")
            if df.empty or len(df) < 26:
                continue

            df["tenkan"] = (df["High"].rolling(window=9).max() + df["Low"].rolling(window=9).min()) / 2
            df["kijun"] = (df["High"].rolling(window=26).max() + df["Low"].rolling(window=26).min()) / 2

            last = df.iloc[-1]
            if last["Close"] > last["tenkan"] > last["kijun"]:
                signals.append(f"🚀 *{ticker}* : Potentiel breakout détecté\nClôture: {last['Close']:.2f}")

        if signals:
            bot = Bot(token=TELEGRAM_TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text="\n\n".join(signals), parse_mode=ParseMode.MARKDOWN)
            return "📢 Breakouts envoyés"
        else:
            return "🟡 Aucun breakout détecté"

    except Exception as e:
        return f"❌ Erreur breakout : {e}"
