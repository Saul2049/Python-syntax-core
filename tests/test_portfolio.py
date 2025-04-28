import pytest
import pandas as pd
import numpy as np
from src import portfolio_backtest, metrics
from src.portfolio_backtest import run_portfolio


def test_portfolio_runs():
    """基本测试：确保投资组合回测可以运行"""
    eq = run_portfolio()
    assert eq.iloc[-1] > 0


def test_portfolio_default():
    """测试默认配置下的投资组合回测"""
    eq = portfolio_backtest.run_portfolio()
    assert isinstance(eq, pd.Series)
    assert eq.name == "equity_total"


def test_portfolio_custom_allocation():
    """测试自定义权重配置"""
    eq1 = portfolio_backtest.run_portfolio({"btc": 0.7, "eth": 0.3})
    eq2 = portfolio_backtest.run_portfolio({"btc": 0.3, "eth": 0.7})

    # 打印调试信息
    print(f"\nDEBUG VALUES:")
    print(f"Portfolio BTC 70%: {eq1.iloc[-1]}")
    print(f"Portfolio BTC 30%: {eq2.iloc[-1]}")

    # 确保两个投资组合都能成功运行并产生合理结果
    assert eq1.iloc[-1] > 0
    assert eq2.iloc[-1] > 0


def test_portfolio_metrics():
    """测试投资组合的回测指标计算"""
    eq = portfolio_backtest.run_portfolio()

    cagr = metrics.cagr(eq)
    mdd = metrics.max_drawdown(eq)
    sharpe = metrics.sharpe_ratio(eq)

    # 打印调试信息
    print(f"\nDEBUG VALUES:")
    print(f"CAGR: {cagr}")
    print(f"Max Drawdown: {mdd}")
    print(f"Sharpe Ratio: {sharpe}")

    # 确保指标在合理范围内
    assert -1 < cagr < 1
    assert mdd <= 0
