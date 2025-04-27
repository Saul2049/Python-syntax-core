import pytest
import pandas as pd
from src import portfolio_backtest, metrics

def test_portfolio_default():
    """测试默认配置下的投资组合回测"""
    eq = portfolio_backtest.run_portfolio()
    assert isinstance(eq, pd.Series)
    assert eq.name == "equity_total"
    assert eq.iloc[-1] > 0
    
def test_portfolio_custom_allocation():
    """测试自定义权重配置"""
    eq1 = portfolio_backtest.run_portfolio({"btc": 0.7, "eth": 0.3})
    eq2 = portfolio_backtest.run_portfolio({"btc": 0.3, "eth": 0.7})
    
    # 确保不同权重产生不同结果
    assert eq1.iloc[-1] != eq2.iloc[-1]
    
def test_portfolio_metrics():
    """测试投资组合的回测指标计算"""
    eq = portfolio_backtest.run_portfolio()
    
    cagr = metrics.cagr(eq)
    mdd = metrics.max_drawdown(eq)
    sharpe = metrics.sharpe_ratio(eq)
    
    # 确保指标在合理范围内
    assert -1 < cagr < 1
    assert mdd <= 0
    assert not pd.isna(sharpe) 