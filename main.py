from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import os
import telegram
from google.oauth2.service_account import Credentials
import gspread
import yfinance as yf
import asyncio

app = FastAPI()

@app.get("/", response_class=PlainTextResponse)
async def root():
    return "✅ Analyse Clôture Render : OK"

# --- Config Telegram
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
bot = telegram.Bot(token=TOKEN)

# --- Google Sheets Auth
SHEET_ID = os.environ['GOOGLE_SHEET_ID']
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = Credentials.from_service_account_file("/etc/secrets/credentials.json", scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).sheet1

# --- Analyse Ichimoku + Volatilité
def analyse_ticker(ticker):
    data = yf.download(ticker, period="3mo", interval="1d")
    if data.empty:
        return f"{ticker} : données introuvables."

    # Ichimoku
    nine_period_high = data['High'].rolling(window=9).max()
    nine_period_low = data['Low'].rolling(window=9).min()
    data['tenkan_sen'] = (nine_period_high + nine_period_low) / 2

    period26_high = data['High'].rolling(window=26).max()
    period26_low = data['Low'].rolling(window=26).min()
    data['kijun_sen'] = (period26_high + period26_low) / 2

    latest = data.iloc[-1]
    if latest['tenkan_sen'] > latest['kijun_sen']:
        tendance = "📈 Signal haussier"
    elif latest['tenkan_sen'] < latest['kijun_sen']:
        tendance = "📉 Signal baissier"
    else:
        tendance = "⚖️ Indécis"

    # Volatilité
    daily_returns = data['Close'].pct_change()
    vol = daily_returns.std() * 100
    return f"{ticker} : {tendance} | Volatilité : {vol:.2f}%"

# --- Tâche principale
@app.get("/analyse", response_class=PlainTextResponse)
async def run_analysis():
    tickers = sheet.col_values(1)[1:]
    results = []

    for ticker in tickers:
        result = analyse_ticker(ticker)
        results.append(result)

        await bot.send_message(chat_id=CHAT_ID, text=result)

    return "\n".join(results)
