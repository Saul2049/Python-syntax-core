import pytest
import pandas as pd
import numpy as np
from src import data, broker, metrics

def test_single_bt_runs():
    """测试 backtest_single 可以正常运行并返回合理的最终权益值"""
    df = data.load_csv()
    eq = broker.backtest_single(df["btc"])
    assert eq.iloc[-1] > 0
    
def test_single_bt_params():
    """测试不同参数对回测结果的影响"""
    df = data.load_csv()
    price = df["btc"]
    
    # 默认参数回测
    eq_default = broker.backtest_single(price)
    
    # 更改 fast 窗口
    eq_fast_small = broker.backtest_single(price, fast_win=3)
    eq_fast_large = broker.backtest_single(price, fast_win=10)
    
    # 更改 slow 窗口
    eq_slow_small = broker.backtest_single(price, slow_win=15)
    eq_slow_large = broker.backtest_single(price, slow_win=30)
    
    # 确认参数变化会导致结果变化
    assert eq_default.iloc[-1] != eq_fast_small.iloc[-1]
    assert eq_default.iloc[-1] != eq_fast_large.iloc[-1]
    assert eq_default.iloc[-1] != eq_slow_small.iloc[-1]
    assert eq_default.iloc[-1] != eq_slow_large.iloc[-1]

def test_single_bt_metrics():
    """测试指标计算的一致性"""
    df = data.load_csv()
    eq = broker.backtest_single(df["btc"])
    
    # 验证指标计算
    assert metrics.cagr(eq) > -1 and metrics.cagr(eq) < 1  # 合理的CAGR范围
    assert metrics.max_drawdown(eq) <= 0  # 回撤应为负值或零
    assert pd.notna(metrics.sharpe_ratio(eq))  # 使用pd.notna替代not pd.isna 