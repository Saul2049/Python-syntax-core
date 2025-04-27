import pandas as pd
import numpy as np
from crossovers import bullish_cross_indices, bearish_cross_indices

df = pd.read_csv("btc_eth.csv", parse_dates=["date"], index_col="date")
price = df["btc"]
fast  = price.rolling(5).mean()
slow  = price.rolling(20).mean()

buy_i  = bullish_cross_indices(fast, slow)
sell_i = bearish_cross_indices(fast, slow)

# --- simple 1-share position, no slippage / fees ------------------------
equity = 100000.0
position = 0        # 0 or 1 share
for i, p in enumerate(price):
    if i in buy_i and position == 0:
        position = 1
        entry    = p
    if i in sell_i and position == 1:
        equity += (p - entry)          # realise P&L
        position = 0

# mark-to-market final position
if position == 1:
    equity += (price.iloc[-1] - entry)

print(f"Final equity: {equity:,.2f} USD")
