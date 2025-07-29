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

async def run_analysis():
    try:
        # Authentification Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_JSON, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        tickers = sheet.col_values(1)[1:]  # en ignorant l'en-tête

        messages = []
        for ticker in tickers:
            data = yf.download(ticker, period="30d", interval="1d")
            if data.empty:
                continue

            # Exemple simple : clôture > Tenkan > Kijun → signal haussier
            data['tenkan'] = (data['High'].rolling(window=9).max() + data['Low'].rolling(window=9).min()) / 2
            data['kijun'] = (data['High'].rolling(window=26).max() + data['Low'].rolling(window=26).min()) / 2
            last = data.iloc[-1]

            if last['Close'] > last['tenkan'] > last['kijun']:
                messages.append(f"📈 *{ticker}* : Signal haussier détecté\nClôture: {last['Close']:.2f}")

        if messages:
            bot = Bot(token=TELEGRAM_TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text="\n\n".join(messages), parse_mode=ParseMode.MARKDOWN)
            return "📬 Alertes envoyées"
        else:
            return "🟡 Aucune alerte détectée"

    except Exception as e:
        return f"❌ Erreur analyseur : {e}"
