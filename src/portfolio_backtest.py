import pandas as pd
from typing import Dict
from src import data, broker


def run_portfolio(alloc: Dict[str, float] = None) -> pd.Series:
    """
    alloc 形如 {"btc":0.5, "eth":0.5}，权重之和 = 1
    返回组合 equity 曲线
    """
    df = data.load_csv()
    if alloc is None:
        alloc = {"btc": 0.5, "eth": 0.5}

    curves = []
    for sym, w in alloc.items():
        curve = broker.backtest_single(
            df[sym], fast_win=7, slow_win=20, atr_win=20, init_equity=100_000 * w
        )
        curves.append(curve)

    # 将各子曲线按索引相加
    total = pd.concat(curves, axis=1).sum(axis=1)
    total.name = "equity_total"
    return total
