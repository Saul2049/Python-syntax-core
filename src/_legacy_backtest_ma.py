import pandas as pd
import numpy as np
from crossovers import bullish_cross_indices, bearish_cross_indices

df = pd.read_csv("btc_eth.csv", parse_dates=["date"], index_col="date")
price = df["btc"]
# calculate ATR(14) for position sizing & stop-loss
tr = pd.DataFrame({
    "hl": price.rolling(2).max() - price.rolling(2).min(),
    "hc": (price - price.shift(1)).abs(),
    "lc": (price - price.shift(1)).abs()
}).max(axis=1)
atr14 = tr.rolling(14).mean()
fast  = price.rolling(3).mean()
slow  = price.rolling(7).mean()

buy_i  = bullish_cross_indices(fast, slow)
sell_i = bearish_cross_indices(fast, slow)

# --- ATR-based sizing & stop-loss backtest ------------------------------
equity = 100_000.0
risk_per_trade = 0.02    # risk 2% of equity per trade
stop_mult = 1            # stop-loss at entry - 1 × ATR
position = 0            # number of shares
entry = 0.0
stop_price = None
equity_curve = []        # record equity at each time step
for i, p in enumerate(price):
    if i in buy_i and position == 0 and not np.isnan(atr14.iloc[i]):
        # size position by ATR risk
        risk_amount = equity * risk_per_trade
        atr = atr14.iloc[i]
        position = max(int(risk_amount / atr), 1)
        entry = p
        stop_price = entry - stop_mult * atr
    if position > 0:
        # stop-loss check
        if p <= stop_price:
            equity += (stop_price - entry) * position
            position = 0
            stop_price = None
            equity_curve.append(equity)
            continue
        # sell on crossover
        if i in sell_i:
            equity += (p - entry) * position
            position = 0
            stop_price = None
    # record equity after daily update
    equity_curve.append(equity)

# mark-to-market any open position
if position > 0:
    equity += (price.iloc[-1] - entry) * position

# convert equity curve list to pandas Series for plotting
equity_series = pd.Series(equity_curve, index=price.index)

print(f"Final equity: {equity:,.2f} USD")

if __name__ == '__main__':
    # plot the equity curve
    import matplotlib.pyplot as plt
    equity_series.plot(title="MA-Crossover Equity Curve")
    plt.xlabel('Date')
    plt.ylabel('Equity (USD)')
    plt.show()

    # --- Benchmark & Performance Metrics ---
    # buy-and-hold benchmark starting with same capital
    buy_hold = price / price.iloc[0] * equity_series.iloc[0]
    # compute CAGR
    days = (price.index[-1] - price.index[0]).days
    years = days / 365.25
    strat_cagr = (equity_series.iloc[-1] / equity_series.iloc[0])**(1/years) - 1
    bh_cagr = (buy_hold.iloc[-1] / buy_hold.iloc[0])**(1/years) - 1
    # compute max drawdown
    strat_dd = (equity_series / equity_series.cummax() - 1).min()
    bh_dd = (buy_hold / buy_hold.cummax() - 1).min()
    # compute Sharpe ratio (assume 252 trading days, no risk-free rate)
    strat_ret = equity_series.pct_change().dropna()
    bh_ret = buy_hold.pct_change().dropna()
    strat_sharpe = strat_ret.mean() / strat_ret.std() * (252**0.5)
    bh_sharpe = bh_ret.mean() / bh_ret.std() * (252**0.5)
    # print metrics
    print(f"Strategy CAGR: {strat_cagr:.2%}, Buy&Hold CAGR: {bh_cagr:.2%}")
    print(f"Strategy Max DD: {strat_dd:.2%}, Buy&Hold Max DD: {bh_dd:.2%}")
    print(f"Strategy Sharpe: {strat_sharpe:.2f}, Buy&Hold Sharpe: {bh_sharpe:.2f}")
