import os
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import matplotlib.pyplot as plt
import gspread
import yfinance as yf
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask

app = Flask(__name__)

# ENV VARIABLES
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_CREDENTIALS_JSON = "/etc/secrets/credentials.json"
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

def send_telegram_image(image_path, caption="📊 Graphique"):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(image_path, 'rb') as photo:
        files = {'photo': photo}
        data = {'chat_id': CHAT_ID, 'caption': caption}
        requests.post(url, files=files, data=data)

def get_tickers_from_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_JSON, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    return sheet.col_values(1)[1:]  # Ignore header

def calculate_ichimoku(df):
    df['Tenkan_sen'] = df['Close'].rolling(window=9).mean()
    df['Kijun_sen'] = df['Close'].rolling(window=26).mean()
    return df

@app.route('/')
def run_analysis():
    try:
        tickers = get_tickers_from_sheet()
        if not tickers:
            return "Aucun ticker trouvé."

        all_signals = []

        for ticker in tickers:
            df = yf.download(ticker, period='90d', interval='1d')
            df = df.reset_index()
            df = df[['Date', 'Open', 'Close', 'Volume']]

            df['Volatility'] = df['Close'].rolling(window=10).std()
            vol_mean = df['Volatility'].mean()
            vol_std = df['Volatility'].std()
            df['Z_score'] = (df['Volatility'] - vol_mean) / vol_std

            df = calculate_ichimoku(df)

            df['Signal'] = np.where(
                (df['Z_score'] > 2) & (df['Close'] > df['Tenkan_sen']) & (df['Close'] > df['Kijun_sen']),
                "📈 Signal haussier",
                np.where(
                    (df['Z_score'] > 2) & (df['Close'] < df['Tenkan_sen']) & (df['Close'] < df['Kijun_sen']),
                    "📉 Signal baissier",
                    ""
                )
            )

            alerts = df[df['Signal'] != ""].tail(3)
            if not alerts.empty:
                all_signals.append((ticker, alerts, df))

        if all_signals:
            messages = []
            for ticker, alerts, full_df in all_signals:
                for _, row in alerts.iterrows():
                    msg = (
                        f"📌 {ticker} - {row['Date'].strftime('%Y-%m-%d')}\n"
                        f"💰 {row['Close']:.2f} | Z={row['Z_score']:.2f}\n"
                        f"{row['Signal']}"
                    )
                    messages.append(msg)

                # Graph
                plt.figure(figsize=(12, 6))
                plt.plot(full_df['Date'], full_df['Close'], label='Clôture', color='blue')
                plt.plot(full_df['Date'], full_df['Tenkan_sen'], label='Tenkan', linestyle='--')
                plt.plot(full_df['Date'], full_df['Kijun_sen'], label='Kijun', linestyle='--')
                plt.title(f"Ichimoku + Volatilité : {ticker}")
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                path = f"/tmp/{ticker}_graph.png"
                plt.savefig(path)
                plt.close()
                send_telegram_image(path, f"📊 {ticker} — Analyse Ichimoku + Volatilité")

            send_telegram_message("\n\n".join(messages))
        else:
            send_telegram_message("✅ Aucun signal détecté aujourd’hui.")
        return "✅ Analyse exécutée avec succès"

    except Exception as e:
        send_telegram_message(f"❌ Erreur : {str(e)}")
        return f"❌ Erreur : {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
