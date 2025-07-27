import yfinance as yf
from telegram import Bot
import os

def analyse_ouverture():
    tickers = ["TSLA", "AAPL", "NVDA"]
    messages = []

    for ticker in tickers:
        df = yf.download(ticker, period="10d", interval="1d")

        if df.empty or len(df) < 10:
            continue

        high9 = df['High'].rolling(window=9).max()
        low9 = df['Low'].rolling(window=9).min()
        tenkan = (high9 + low9) / 2

        high26 = df['High'].rolling(window=26).max()
        low26 = df['Low'].rolling(window=26).min()
        kijun = (high26 + low26) / 2

        close = df['Close']
        close_1 = close.iloc[-2]
        tenkan_1 = tenkan.iloc[-2]
        kijun_1 = kijun.iloc[-2]

        if tenkan_1 > kijun_1 and close_1 > tenkan_1:
            messages.append(f"📊 {ticker} : Signal haussier pour l’ouverture.")

    if messages:
        message_final = "\n".join(messages)
    else:
        message_final = "Aucun signal d’achat à l’ouverture."

    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("CHAT_ID")
    if token and chat_id:
        bot = Bot(token=token)
        bot.send_message(chat_id=chat_id, text=message_final)

    return message_final
