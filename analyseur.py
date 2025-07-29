import os
import gspread
import yfinance as yf
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot
from telegram.constants import ParseMode

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDS_JSON = "/etc/secrets/credentials.json"

async def run():
    try:
        # Authentification Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_JSON, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        tickers = sheet.col_values(1)[1:]  # Ignore l'en-tête

        messages = []

        for ticker in tickers:
            try:
                df = yf.download(ticker, period="2mo", interval="1d")
                if df.empty or len(df) < 26:
                    continue

                # Ichimoku - Conversion & Base Line
                nine_period_high = df['High'].rolling(window=9).max()
                nine_period_low = df['Low'].rolling(window=9).min()
                df['tenkan_sen'] = (nine_period_high + nine_period_low) / 2

                period26_high = df['High'].rolling(window=26).max()
                period26_low = df['Low'].rolling(window=26).min()
                df['kijun_sen'] = (period26_high + period26_low) / 2

                last = df.iloc[-1]
                if last['tenkan_sen'] > last['kijun_sen']:
                    messages.append(f"📈 *Signal Ichimoku haussier détecté sur {ticker}*")

            except Exception as e:
                messages.append(f"⚠️ Erreur avec {ticker} : {e}")

        bot = Bot(token=TELEGRAM_TOKEN)
        if messages:
            for msg in messages:
                await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
        else:
            await bot.send_message(chat_id=CHAT_ID, text="Aucun signal détecté aujourd'hui.")

        return {"message": "Analyse terminée avec succès"}

    except Exception as e:
        return {"message": f"Erreur dans l'analyseur : {e}"}
