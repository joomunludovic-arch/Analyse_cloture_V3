import os
import json
import gspread
import yfinance as yf
from fastapi import FastAPI
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot

# Initialisation FastAPI
app = FastAPI()

# Chargement du token Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Chargement des credentials Google
with open("/etc/secrets/credentials.json") as f:
    creds_data = json.load(f)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)
client = gspread.authorize(creds)

# Accès à Google Sheet
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
sheet = client.open_by_key(SHEET_ID).sheet1

def fetch_tickers():
    return [cell for cell in sheet.col_values(1) if cell and cell != "TICKERS"]

def analyze_ticker(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d")
        if len(data) < 26:
            return f"{ticker} : Pas assez de données"

        # Volatilité simple (écart-type des variations %)
        data["returns"] = data["Close"].pct_change()
        volatility = data["returns"].std() * 100

        # Ichimoku : Tenkan-sen et Kijun-sen
        nine_period_high = data['High'].rolling(window=9).max()
        nine_period_low = data['Low'].rolling(window=9).min()
        tenkan_sen = (nine_period_high + nine_period_low) / 2

        period26_high = data['High'].rolling(window=26).max()
        period26_low = data['Low'].rolling(window=26).min()
        kijun_sen = (period26_high + period26_low) / 2

        signal = ""
        if tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]:
            signal = "Signal haussier 📈"
        elif tenkan_sen.iloc[-1] < kijun_sen.iloc[-1]:
            signal = "Signal baissier 📉"
        else:
            signal = "Neutre ⚖️"

        return f"{ticker} : {signal} | Volatilité : {volatility:.2f}%"
    except Exception as e:
        return f"{ticker} : Erreur - {str(e)}"

def send_alert(messages):
    bot = Bot(token=TELEGRAM_TOKEN)
    for msg in messages:
        bot.send_message(chat_id=CHAT_ID, text=msg)

@app.get("/")
def launch_analysis():
    tickers = fetch_tickers()
    results = [analyze_ticker(ticker) for ticker in tickers]
    send_alert(results)
    return {"status": "OK", "results": results}
