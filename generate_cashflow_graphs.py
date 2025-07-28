import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime, timedelta

tickers = ['TSLA', 'NVDA', 'AAPL', 'AMD', 'META', 'NFLX', 'AMZN', 'COIN', 'PLTR', 'MARA']
output_dir = "cashflow_graphs"
os.makedirs(output_dir, exist_ok=True)

start_date = datetime.now() - timedelta(days=30)
for ticker in tickers:
    data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), interval='1d')
    if data.empty or len(data) < 10:
        continue

    data['Volatility'] = data['Close'].pct_change().rolling(window=5).std()

    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data['Close'], label='Clôture')
    plt.plot(data.index, data['Volatility'], label='Volatilité (5j)', linestyle='--')
    plt.title(f"{ticker} - Clôture & Volatilité")
    plt.xlabel("Date")
    plt.ylabel("Prix / Volatilité")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    path = f"{output_dir}/{ticker}_volatility.png"
    plt.savefig(path)
    plt.close()

print(f"{len(tickers)} graphiques enregistrés dans le dossier : {output_dir}")
