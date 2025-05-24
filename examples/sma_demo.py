from src import data, signals

df = data.load_csv()
sma_5 = signals.moving_average(df["btc"], 5)
print(sma_5.tail())
