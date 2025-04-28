# src/metrics.py
import pandas as pd
import numpy as np

TRADING_DAYS = 252  # 可按需要修改


def cagr(equity: pd.Series) -> float:
    """复合年化收益率 (CAGR)。"""
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    return (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1


def max_drawdown(equity: pd.Series) -> float:
    """最大回撤（负值）。"""
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    return drawdown.min()


def sharpe_ratio(equity: pd.Series, rf: float = 0.0) -> float:
    """年化 Sharpe。rf 传年化无风险收益率。"""
    rets = equity.pct_change().dropna()
    excess = rets - rf / TRADING_DAYS
    std = excess.std(ddof=0)
    # std为零 -> 恒定序列，返回NaN
    if std == 0:
        return np.nan
    # std为NaN -> 返回0.0
    if np.isnan(std):
        return 0.0
    return np.sqrt(TRADING_DAYS) * excess.mean() / std
