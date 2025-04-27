# test_backtest.py
from backtest_ma import equity

def test_equity_positive():
    """
    Smoke test: ensure the backtest doesn't lose all capital.
    """
    assert equity > 0  # toy check: you didn't lose everything! 