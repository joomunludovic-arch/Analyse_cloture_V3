import yfinance as yf
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import telegram

# Config Google Sheets
SHEET_ID = "1-hPKh5yJq6F-eboLbsG8sLxwdesI9LPH2L08emI7i6g"
RANGE = "Feuille1!A:A"

# Config Telegram
BOT_TOKEN = "TON_TOKEN_TELEGRAM"
CHAT_ID = "TON_CHAT_ID"

def get_tickers():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    tickers = sheet.worksheet("Feuille1").col_values(1)[1:]  # ignore header
    return tickers

def analyse_ticker(ticker):
    df = yf.download(ticker, period="1mo", interval="1d")
    if df.empty:
        return None

    # Ichimoku simplifié : nuage = kijun (26) vs tenkan (9)
    df["tenkan"] = (df["High"].rolling(9).max() + df["Low"].rolling(9).min()) / 2
    df["kijun"] = (df["High"].rolling(26).max() + df["Low"].rolling(26).min()) / 2

    # Volatilité simple
    df["volatility"] = df["Close"].rolling(5).std()

    signal = ""
    if df["tenkan"].iloc[-1] > df["kijun"].iloc[-1]:
        signal += "🟢 Tendance haussière Ichimoku\n"
    if df["volatility"].iloc[-1] > df["volatility"].mean():
        signal += "⚠️ Forte volatilité\n"

    return signal if signal else None

def main():
    bot = telegram.Bot(token=BOT_TOKEN)
    tickers = get_tickers()

    for ticker in tickers:
        signal = analyse_ticker(ticker)
        if signal:
            msg = f"🔔 Signal sur {ticker} :\n{signal}"
            bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    main()
