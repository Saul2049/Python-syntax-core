import pandas as pd
df = pd.read_csv("btc_eth.csv", parse_dates=["date"], index_col="date")
sma_5 = df["btc"].rolling(5).mean()
print("Last five 5-day SMA values:")
print(sma_5.tail())
